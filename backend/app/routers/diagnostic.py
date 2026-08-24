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
        shop_id=UUID(shop_id),
        brand=payload.brand,
        model=payload.model,
        symptom=payload.symptom
    )
    if not search_result.had_sufficient_evidence or not search_result.cases:
        return {"suggestion": "No hay suficientes casos similares para sugerir."}
        
    best = search_result.cases[0]
    return {
        "suggestion": f"Basado en casos anteriores de {payload.brand} {payload.model}: Posible {best.diagnosed_cause}. Solución: {best.solution_applied}."
    }


# ═════════════════════════════════════════════════════════════════════════════
# POST /diagnostic/chat — Copiloto IA Técnico Libre
# ═════════════════════════════════════════════════════════════════════════════
import uuid
from google import genai
from google.genai import types
from fastapi import Request
from app.config import get_settings
from app.core.rate_limit import limiter, get_user_rate_limit_key
from app.schemas.diagnostic import DiagnosticMessageIn, DiagnosticMessageResponse


@router.post(
    "/chat",
    response_model=DiagnosticMessageResponse,
    summary="Chat técnico libre / Copiloto de taller",
    description="Consulta técnica libre con el copiloto IA (Gemini 3.7 Flash) para asistencia en diagnósticos y reparaciones.",
)
@limiter.limit("10/minute", key_func=get_user_rate_limit_key)
async def workshop_diagnostic_chat(
    request: Request,
    payload: DiagnosticMessageIn,
    current_user: User = Depends(subscription_guard),
):
    settings = get_settings()
    prompt = (
        "Eres un copiloto técnico experto en microelectrónica, reparación de hardware, telefonía móvil, "
        "computadoras y electrodomésticos para talleres profesionales.\n"
        "Proporciona respuestas concisas, altamente técnicas, prácticas y ordenadas paso a paso para asistir al técnico.\n\n"
        f"Consulta del técnico:\n{payload.message}"
    )

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-3.7-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        ai_reply = response.text or "No se pudo generar una respuesta del copiloto en este momento."
    except Exception as exc:
        ai_reply = f"Servicio de Copiloto IA no disponible temporalmente: {str(exc)}"

    return DiagnosticMessageResponse(
        id=uuid.uuid4(),
        role="assistant",
        content=ai_reply,
        created_at=datetime.now(timezone.utc),
    )
