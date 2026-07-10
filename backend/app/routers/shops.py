"""
Router: POST /shops — Onboarding completo de un nuevo taller.

Crea en una sola transacción atómica:
  - Shop con trial de 30 días
  - Subscription con status='trial' (fuente de verdad — D1)
  - Primer usuario admin (Riesgo 2)

Regla 1: No solicita datos de pago.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.shop import ShopCreate, ShopOnboardingResponse, ShopResponse
from app.services.shop_service import create_shop

router = APIRouter(prefix="/shops", tags=["shops"])


@router.post(
    "",
    response_model=ShopOnboardingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear taller (onboarding)",
    description=(
        "Crea un nuevo taller con prueba gratuita de 30 días, su suscripción trial "
        "y el primer usuario administrador. Sin datos de pago (Regla 1)."
    ),
)
async def create_shop_endpoint(
    payload: ShopCreate,
    db: AsyncSession = Depends(get_db),
) -> ShopOnboardingResponse:
    """
    POST /shops
    Smoke tests: ST-06 y ST-07.
    """
    try:
        shop, admin_email = await create_shop(db, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except IntegrityError as exc:
        # Subdomain duplicado o admin_email ya registrado
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El subdomain o el email del administrador ya están en uso.",
        ) from exc

    return ShopOnboardingResponse(
        shop=ShopResponse.model_validate(shop),
        admin_email=admin_email,
    )

