import asyncio
import uuid
import json
from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
import logging
from google import genai
from google.genai import types, errors

from app.config import get_settings
from app.models.diagnostic import DiagnosticConversation, DiagnosticMessage, DiagnosticCase, DiagnosticQueryLog
from app.models.ticket import Ticket
from app.schemas.diagnostic import DiagnosticMessageIn, DiagnosticMessageResponse, ConfirmCorrectionIn, DiagnosticCaseResponse
from app.services.embedding_service import EmbeddingService
from app.services.model_router import ModelRouter
from app.services.llm_gateway import generate_llm_content
from app.services.tavily_service import search_technical_web
from app.services.ai_safety_service import (
    classify_message_safety,
    evaluate_web_research_intent,
    log_ai_security_event,
    CANNED_REDIRECT_RESPONSE,
    ANTI_INJECTION_SYSTEM_INSTRUCTION,
    SANDWICH_PROMPT_REMINDER,
)

logger = logging.getLogger(__name__)

class CorrectionService:
    @staticmethod
    async def get_or_create_conversation(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID) -> DiagnosticConversation:
        stmt = select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket_id,
            DiagnosticConversation.shop_id == shop_id,
            DiagnosticConversation.technician_id == technician_id,
            DiagnosticConversation.status == "open"
        )
        result = await db.execute(stmt)
        conv = result.scalar_one_or_none()
        
        if not conv:
            log_stmt = select(DiagnosticQueryLog).where(
                DiagnosticQueryLog.ticket_id == ticket_id
            ).order_by(DiagnosticQueryLog.created_at.desc()).limit(1)
            log_result = await db.execute(log_stmt)
            log_entry = log_result.scalar_one_or_none()
            
            top_case_id = log_entry.top_case_id if log_entry else None

            conv = DiagnosticConversation(
                ticket_id=ticket_id,
                technician_id=technician_id,
                shop_id=shop_id,
                diagnostic_case_id=top_case_id,
                status="open"
            )
            db.add(conv)
            try:
                await db.commit()
                await db.refresh(conv)
            except IntegrityError:
                # The partial unique index is the authority when two requests
                # attempt to open the same ticket chat at the same time.
                await db.rollback()
                conv = await db.scalar(stmt)
                if conv is None:
                    raise
            
            
        return conv

    @staticmethod
    async def handle_chat_message(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID, message_in: DiagnosticMessageIn) -> DiagnosticMessageResponse:
        conv = await CorrectionService.get_or_create_conversation(db, shop_id, technician_id, ticket_id)
        conv_id = conv.id
        
        user_msg = DiagnosticMessage(
            conversation_id=conv_id,
            role="technician",
            content=message_in.message
        )
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)

        safety = await classify_message_safety(message_in.message)
        if safety.injection_attempt or not safety.on_topic:
            if safety.injection_attempt:
                await log_ai_security_event(
                    db=db,
                    shop_id=shop_id,
                    technician_id=technician_id,
                    ticket_id=ticket_id,
                    event_type="injection_attempt",
                    message_excerpt=message_in.message,
                )
            asst_msg = DiagnosticMessage(
                conversation_id=conv_id,
                role="assistant",
                content=CANNED_REDIRECT_RESPONSE,
            )
            db.add(asst_msg)
            await db.commit()
            await db.refresh(asst_msg)

            return DiagnosticMessageResponse(
                id=asst_msg.id,
                role=asst_msg.role,
                content=asst_msg.content,
                created_at=asst_msg.created_at,
                model_route="safety_guard",
                model="canned",
            )

        stmt = select(DiagnosticMessage).where(DiagnosticMessage.conversation_id == conv_id).order_by(DiagnosticMessage.created_at.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_res = await db.execute(ticket_stmt)
        ticket = ticket_res.scalar_one_or_none()
        
        sources = []
        if message_in.deep_research:
            should_search = evaluate_web_research_intent(
                message=message_in.message,
                llm_intent=safety.web_research_intent,
            )
            if should_search:
                device_query_context = f"{ticket.device_brand} {ticket.device_model}" if ticket else ""
                sources = await search_technical_web(
                    query=message_in.message,
                    device_context=device_query_context,
                )
            else:
                logger.info(
                    "Skipping Tavily search: query lacks concrete web research intent (vague or introductory query).",
                    extra={"query_excerpt": message_in.message[:80]},
                )

        settings = get_settings()
        route = ModelRouter.select(message_in.message, ticket_context=True, prior_messages=messages[:-1])
        chosen_tier = "reasoning" if message_in.deep_research else route.route
        chosen_max_tokens = 1500 if message_in.deep_research else route.max_output_tokens
        chosen_timeout = (
            settings.gemini_deep_research_timeout_seconds
            if message_in.deep_research
            else settings.gemini_primary_timeout_seconds
        )

        history = "\n".join(f"{msg.role}: {msg.content[:800]}" for msg in messages[-8:])
        device_context = f"Device: {ticket.device_brand} {ticket.device_model}. Symptom: {ticket.issue_description}." if ticket else ""

        web_context_prompt = ""
        if sources:
            web_context_prompt = (
                "\nVerified Technical Web Findings (Schematics & Community Fixes):\n"
                + "\n".join(f"- {s['title']}: {s['content']}" for s in sources)
                + "\nUse this technical web information to provide deeper, precise troubleshooting steps.\n"
            )

        prompt = (
            "You are Ohm, a repair technician assistant. Give concise, actionable steps. "
            "Do not repeat the ticket context.\n"
            f"{ANTI_INJECTION_SYSTEM_INSTRUCTION}\n"
            f"{device_context}\n"
            f"{web_context_prompt}"
            f"Recent chat:\n{history}\n"
            f"{SANDWICH_PROMPT_REMINDER}"
        )
            
        resolved_model = route.model
        retries = 3
        backoff_delays = [1.0, 2.0, 4.0]
        llm_res = None
        for attempt in range(retries):
            try:
                llm_res = await generate_llm_content(
                    prompt=prompt,
                    tier=chosen_tier,
                    temperature=0.0,
                    max_output_tokens=chosen_max_tokens,
                    timeout_seconds=chosen_timeout,
                )
                break
            except Exception as e:
                is_503 = (
                    (isinstance(e, errors.APIError) and getattr(e, "code", None) == 503)
                    or getattr(e, "code", None) == 503
                    or getattr(e, "status_code", None) == 503
                    or "503" in str(e)
                )
                if is_503 and attempt < retries - 1:
                    logger.warning(f"Gemini 503 Service Unavailable on attempt {attempt + 1}/{retries}. Retrying in {backoff_delays[attempt]}s...")
                    await asyncio.sleep(backoff_delays[attempt])
                    continue
                elif is_503:
                    logger.error(f"Gemini 503 Service Unavailable exhausted all {retries} retries.")
                    ai_reply = "Servicio de Ohm no disponible temporalmente por alta demanda (503). Por favor intenta de nuevo en unos momentos."
                    break
                else:
                    logger.error(f"Error generating diagnostic message: {e}")
                    ai_reply = f"Servicio de Ohm no disponible temporalmente: {str(e)}"
                    break
        else:
            if llm_res is None:
                ai_reply = "Servicio de Ohm no disponible temporalmente por alta demanda (503). Por favor intenta de nuevo en unos momentos."
            else:
                ai_reply = llm_res.text or "I understand. Let's adjust the diagnosis."

        if llm_res is not None:
            ai_reply = llm_res.text or "I understand. Let's adjust the diagnosis."
            resolved_model = llm_res.model_used
        
        if sources:
            sources_footer = "\n\n---\n**Fuentes consultadas:**\n" + "\n".join(
                f"- [{s['title']}]({s['url']})" for s in sources
            )
            ai_reply = f"{ai_reply.rstrip()}{sources_footer}"

        asst_msg = DiagnosticMessage(
            conversation_id=conv.id,
            role="assistant",
            content=ai_reply
        )
        db.add(asst_msg)
        await db.commit()
        await db.refresh(asst_msg)
        
        return DiagnosticMessageResponse(
            id=asst_msg.id,
            role=asst_msg.role,
            content=asst_msg.content,
            created_at=asst_msg.created_at,
            model_route=chosen_tier,
            model=resolved_model,
            sources=sources if sources else None,
        )

    @staticmethod
    async def get_conversation_history(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID) -> list[DiagnosticMessageResponse]:
        """Return only the caller's open ticket thread; never cross technician boundaries."""
        conversation = await db.scalar(select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket_id,
            DiagnosticConversation.shop_id == shop_id,
            DiagnosticConversation.technician_id == technician_id,
            DiagnosticConversation.status == "open",
        ))
        if not conversation:
            return []
        result = await db.execute(select(DiagnosticMessage).where(
            DiagnosticMessage.conversation_id == conversation.id
        ).order_by(DiagnosticMessage.created_at.asc()))
        return [DiagnosticMessageResponse(id=item.id, role=item.role, content=item.content, created_at=item.created_at)
                for item in result.scalars().all()]

    @staticmethod
    async def confirm_correction(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID, confirm_in: ConfirmCorrectionIn) -> DiagnosticCaseResponse:
        stmt = select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket_id,
            DiagnosticConversation.shop_id == shop_id,
            DiagnosticConversation.technician_id == technician_id,
            DiagnosticConversation.status == "open"
        )
        result = await db.execute(stmt)
        conv = result.scalar_one_or_none()
        
        if not conv:
            raise ValueError("No open conversation found")
            
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_res = await db.execute(ticket_stmt)
        ticket = ticket_res.scalar_one_or_none()
        
        doc_text = EmbeddingService.format_document_text(
            brand=ticket.device_brand,
            model=ticket.device_model,
            symptom=ticket.issue_description,
            cause=confirm_in.diagnosed_cause,
            solution=confirm_in.solution_applied
        )
        
        embedding = await EmbeddingService.get_embedding(doc_text, is_query=False)
        
        new_case = DiagnosticCase(
            shop_id=shop_id,
            origin_ticket_id=ticket_id,
            derived_from_case_id=conv.diagnostic_case_id,
            source_type='real_validated',
            device_brand=ticket.device_brand,
            device_model=ticket.device_model,
            symptom_text=ticket.issue_description,
            diagnosed_cause=confirm_in.diagnosed_cause,
            solution_applied=confirm_in.solution_applied,
            repair_time_minutes=confirm_in.repair_time_minutes,
            estimated_cost=confirm_in.estimated_cost,
            embedding=embedding
        )
        
        db.add(new_case)
        
        from app.models.base import _utcnow
        conv.status = 'confirmed'
        conv.closed_at = _utcnow()
        db.add(conv)
        
        await db.commit()
        await db.refresh(new_case)
        
        return DiagnosticCaseResponse(
            id=new_case.id,
            source_type=new_case.source_type,
            device_brand=new_case.device_brand,
            device_model=new_case.device_model,
            symptom_text=new_case.symptom_text,
            diagnosed_cause=new_case.diagnosed_cause,
            solution_applied=new_case.solution_applied
        )

    @staticmethod
    async def generate_final_diagnostic(db: AsyncSession, ticket: Ticket) -> str:
        """
        Sintetiza la conversación técnica con Ohm en un diagnóstico comprensible
        para el cliente final y lo guarda como borrador (draft_diagnostic).
        """
        stmt = select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket.id,
            DiagnosticConversation.shop_id == ticket.shop_id,
        ).order_by(DiagnosticConversation.created_at.desc())
        result = await db.execute(stmt)
        convs = result.scalars().all()
        if not convs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay conversación previa con Ohm para sintetizar."
            )

        conv_ids = [c.id for c in convs]
        msg_stmt = select(DiagnosticMessage).where(
            DiagnosticMessage.conversation_id.in_(conv_ids)
        ).order_by(DiagnosticMessage.created_at.asc())
        msg_res = await db.execute(msg_stmt)
        messages = msg_res.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay conversación previa con Ohm para sintetizar."
            )

        settings = get_settings()
        client = genai.Client(api_key=settings.gemini_api_key)

        transcript = "\n".join([f"[{m.role.upper()}]: {m.content}" for m in messages])
        synthesis_prompt = (
            f"Eres Ohm, el copiloto técnico experto de TecniDesk.\n"
            f"Tu tarea es redactar el DIAGNÓSTICO FINAL TÉCNICO Y PROCEDIMIENTO REALIZADO para entregar al CLIENTE FINAL (propietario del equipo).\n\n"
            f"INFORMACIÓN DEL EQUIPO:\n"
            f"- Marca y Modelo: {ticket.device_brand} {ticket.device_model}\n"
            f"- Problema Reportado: {ticket.issue_description}\n\n"
            f"HISTORIAL DE CONVERSACIÓN TÉCNICA:\n"
            f"{transcript}\n\n"
            f"DIRECTIVAS ESTRICTAS DE REDACCIÓN:\n"
            f"1. Escribe en tono profesional, empático y claro, apto para el cliente.\n"
            f"2. Explica la causa raíz confirmada durante la revisión/reparación y qué solución o cambio se aplicó.\n"
            f"3. NO uses jerga interna confusa ni nombres de pines o diagramas esquemáticos.\n"
            f"4. NO menciones hipótesis que fueron descartadas durante la conversación.\n"
            f"5. NO inventes procedimientos o repuestos que no aparezcan en el historial.\n"
            f"6. Entrega directamente el texto del diagnóstico sin preámbulos, títulos ni despedidas meta."
        )

        ai_text = None
        try:
            llm_res = await generate_llm_content(
                prompt=synthesis_prompt,
                tier="reasoning",
            )
            ai_text = llm_res.text.strip() if llm_res and llm_res.text else None
        except Exception as e:
            is_503 = (
                (isinstance(e, errors.APIError) and getattr(e, "code", None) == 503)
                or getattr(e, "code", None) == 503
                or getattr(e, "status_code", None) == 503
                or "503" in str(e)
            )
            if is_503:
                logger.error(f"Gemini 503 Service Unavailable for diagnostic synthesis: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Ohm no está disponible temporalmente por alta demanda (503). Intenta de nuevo en unos momentos."
                )
            else:
                logger.error(f"Error calling Gemini for diagnostic synthesis: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Error al generar diagnóstico con Ohm: {str(e)}"
                )

        if not ai_text:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Ohm no generó una respuesta válida para el diagnóstico."
            )

        ticket.draft_diagnostic = ai_text
        await db.commit()
        return ai_text

    @staticmethod
    async def apply_final_diagnostic(
        db: AsyncSession, ticket: Ticket, edited_diagnostic: str | None = None
    ) -> Ticket:
        """
        Aplica el borrador de diagnóstico generado por Ohm a las notas públicas del ticket,
        permitiendo una versión editada opcionalmente por el técnico.
        """
        if ticket.draft_diagnostic is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay un diagnóstico generado para aplicar."
            )

        clean_edit = edited_diagnostic.strip() if edited_diagnostic and edited_diagnostic.strip() else None
        final_text = clean_edit or ticket.draft_diagnostic

        ticket.draft_diagnostic = final_text
        ticket.diagnostic_notes = final_text
        ticket.diagnostic_applied_at = datetime.now(timezone.utc)

        await db.commit()
        return ticket
