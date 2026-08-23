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
