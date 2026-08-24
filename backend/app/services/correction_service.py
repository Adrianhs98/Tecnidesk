import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from google import genai
from google.genai import types

from app.config import get_settings
from app.models.diagnostic import DiagnosticConversation, DiagnosticMessage, DiagnosticCase, DiagnosticQueryLog
from app.models.ticket import Ticket
from app.schemas.diagnostic import DiagnosticMessageIn, DiagnosticMessageResponse, ConfirmCorrectionIn, DiagnosticCaseResponse
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class CorrectionService:
    @staticmethod
    async def get_or_create_conversation(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID) -> DiagnosticConversation:
        stmt = select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket_id,
            DiagnosticConversation.shop_id == shop_id,
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
            await db.commit()
            await db.refresh(conv)
            
        return conv

    @staticmethod
    async def handle_chat_message(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID, message_in: DiagnosticMessageIn) -> DiagnosticMessageResponse:
        conv = await CorrectionService.get_or_create_conversation(db, shop_id, technician_id, ticket_id)
        
        user_msg = DiagnosticMessage(
            conversation_id=conv.id,
            role="technician",
            content=message_in.message
        )
        db.add(user_msg)
        await db.commit()
        await db.refresh(user_msg)
        
        stmt = select(DiagnosticMessage).where(DiagnosticMessage.conversation_id == conv.id).order_by(DiagnosticMessage.created_at.asc())
        result = await db.execute(stmt)
        messages = result.scalars().all()
        
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_res = await db.execute(ticket_stmt)
        ticket = ticket_res.scalar_one_or_none()
        
        prompt = f"You are a master technician assistant helping a technician refine a diagnosis.\n"
        prompt += f"Device: {ticket.device_brand} {ticket.device_model}\nSymptom: {ticket.issue_description}\n\n"
        prompt += "Chat History:\n"
        for msg in messages:
            prompt += f"{msg.role}: {msg.content}\n"
            
        settings = get_settings()
        client = genai.Client(api_key=settings.gemini_api_key)
        
        response = await client.aio.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0)
        )
        
        ai_reply = response.text or "I understand. Let's adjust the diagnosis."
        
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
            created_at=asst_msg.created_at
        )

    @staticmethod
    async def confirm_correction(db: AsyncSession, shop_id: uuid.UUID, technician_id: uuid.UUID, ticket_id: uuid.UUID, confirm_in: ConfirmCorrectionIn) -> DiagnosticCaseResponse:
        stmt = select(DiagnosticConversation).where(
            DiagnosticConversation.ticket_id == ticket_id,
            DiagnosticConversation.shop_id == shop_id,
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
