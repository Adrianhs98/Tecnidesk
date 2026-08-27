from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.core.dependencies import subscription_guard
from app.models.diagnostic import DiagnosticQueryLog
from app.schemas.diagnostic import MaturityMetricResponse
from app.services.diagnostic_service import search_similar_cases
from app.models.user import User

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


def dashboard_ticket_filters(shop_id, technician_id, normalized: str, *, today=None):
    """Build cumulative filters for deterministic technician dashboard queries."""
    today = today or datetime.now(timezone.utc).date()
    filters = [Ticket.shop_id == shop_id, Ticket.technician_id == technician_id]
    if "ayer" in normalized:
        filters.append(func.date(Ticket.created_at) == today - timedelta(days=1))
    elif "hoy" in normalized:
        filters.append(func.date(Ticket.created_at) == today)
    if "pendiente" in normalized or "a medias" in normalized:
        filters.append(Ticket.status.notin_((
            TicketStatusEnum.LISTO_PARA_RETIRAR,
            TicketStatusEnum.NO_APROBADO,
        )))
    return filters

@router.get("/maturity-metric", response_model=MaturityMetricResponse)
async def get_maturity_metric(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(subscription_guard)
):
    shop_id = current_user.shop_id
    """
    Returns the percentage of diagnoses served by real_validated data in the last 30 days.
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    stmt = select(
        func.count(DiagnosticQueryLog.id).label("total_queries"),
        func.sum(
            func.cast(DiagnosticQueryLog.source_type_used == "real_validated", func.integer)
        ).label("real_validated_count"),
        func.sum(
            func.cast(DiagnosticQueryLog.source_type_used == "synthetic", func.integer)
        ).label("synthetic_count")
    ).where(
        DiagnosticQueryLog.shop_id == shop_id,
        DiagnosticQueryLog.created_at >= thirty_days_ago
    )
    
    result = await db.execute(stmt)
    row = result.first()
    
    total = row.total_queries or 0
    real_count = row.real_validated_count or 0
    synth_count = row.synthetic_count or 0
    
    if total == 0:
        return MaturityMetricResponse(
            total_queries=0,
            real_validated_percentage=0.0,
            synthetic_percentage=0.0
        )
        
    return MaturityMetricResponse(
        total_queries=total,
        real_validated_percentage=round((real_count / total) * 100, 2),
        synthetic_percentage=round((synth_count / total) * 100, 2)
    )

class PreviewRequest(BaseModel):
    brand: str
    model: str
    symptom: str

@router.post("/preview")
async def preview_diagnosis(
    payload: PreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(subscription_guard)
):
    shop_id = current_user.shop_id
    """
    Lightweight endpoint for initial suggestion preview (onBlur).
    """
    # Just do a quick retrieval without heavy LLM thinking
    search_result = await search_similar_cases(
        db=db,
        shop_id=shop_id,  # already a UUID from current_user.shop_id
        device_brand=payload.brand,
        device_model=payload.model,
        symptom_text=payload.symptom,
    )
    if not search_result.had_sufficient_evidence or not search_result.cases:
        return {"suggestion": "No hay suficientes casos similares para sugerir."}
        
    best = search_result.cases[0]
    return {
        "suggestion": f"Basado en casos anteriores de {payload.brand} {payload.model}: Posible {best.diagnosed_cause}. Solución: {best.solution_applied}."
    }


# ═════════════════════════════════════════════════════════════════════════════
# POST /diagnostic/chat — Ohm — Asistente IA Técnico Libre
# ═════════════════════════════════════════════════════════════════════════════
import uuid
from google import genai
from google.genai import types
from fastapi import Request
from app.config import get_settings
from app.core.rate_limit import limiter, get_user_rate_limit_key
from app.schemas.diagnostic import DiagnosticMessageIn, DiagnosticMessageResponse
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.technician import Technician
from app.services.model_router import ModelRouter


@router.post(
    "/chat",
    response_model=DiagnosticMessageResponse,
    summary="Chat técnico libre / Ohm (Asistente de taller)",
    description="Consulta técnica libre con el Ohm (Gemini 3.6 Flash) para asistencia en diagnósticos y reparaciones.",
)
@limiter.limit("10/minute", key_func=get_user_rate_limit_key)
async def workshop_diagnostic_chat(
    request: Request,
    payload: DiagnosticMessageIn,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    normalized = payload.message.lower()
    tech = await db.scalar(select(Technician).where(
        Technician.user_id == current_user.id, Technician.shop_id == current_user.shop_id
    ))
    # Dashboard ticket questions are deterministic data requests, not LLM work.
    if tech and any(token in normalized for token in ("pendiente", "ayer", "hoy", "a medias")):
        filters = dashboard_ticket_filters(current_user.shop_id, tech.id, normalized)
        tickets = (await db.execute(select(Ticket).where(*filters).order_by(Ticket.created_at.desc()).limit(10))).scalars().all()
        labels = [f"{item.device_brand} {item.device_model} ({item.status.value if hasattr(item.status, 'value') else item.status})" for item in tickets]
        answer = "No encontré tickets que coincidan." if not labels else "Tickets: " + "; ".join(labels)
        return DiagnosticMessageResponse(id=uuid.uuid4(), role="assistant", content=answer, created_at=datetime.now(timezone.utc), model_route="database", model="database")
    route = ModelRouter.select(payload.message, ticket_context=False)
    prompt = (
        "You are Ohm, a workshop assistant. Answer briefly with practical repair steps.\n"
        f"Question: {payload.message}"
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = await client.aio.models.generate_content(
            model=route.model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=route.max_output_tokens),
        )
        ai_reply = response.text or "No se pudo generar una respuesta de Ohm en este momento."
    except Exception as exc:
        ai_reply = f"Servicio de Ohm no disponible temporalmente: {str(exc)}"

    return DiagnosticMessageResponse(
        id=uuid.uuid4(),
        role="assistant",
        content=ai_reply,
        created_at=datetime.now(timezone.utc),
        model_route=route.route,
        model=route.model,
    )
