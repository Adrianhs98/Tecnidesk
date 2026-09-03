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

from app.core.dependencies import admin_guard, subscription_guard
from app.database import get_db
from app.models.user import User
from app.schemas.shop import (
    ShopCreate,
    ShopOnboardingResponse,
    ShopResponse,
    SlaConfigResponse,
    SlaConfigUpdate,
)
from app.services.shop_service import (
    create_shop,
    get_shop_sla_config,
    update_shop_sla_config,
)

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


@router.get(
    "/sla-config",
    response_model=SlaConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener configuración de SLAs del taller",
    description="Retorna los umbrales efectivos, configuraciones personalizadas y defaults del sistema.",
)
async def get_shop_sla_config_endpoint(
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
) -> SlaConfigResponse:
    """
    GET /shops/sla-config
    Requiere usuario activo del taller y suscripción activa.
    """
    try:
        config = await get_shop_sla_config(db, current_user.shop_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SlaConfigResponse(**config)


@router.patch(
    "/sla-config",
    response_model=SlaConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar configuración de SLAs del taller",
    description="Actualiza los umbrales personalizados de SLA para el taller autenticado.",
)
async def update_shop_sla_config_endpoint(
    payload: SlaConfigUpdate,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
) -> SlaConfigResponse:
    """
    PATCH /shops/sla-config
    Requiere rol de administrador y suscripción activa.
    """
    try:
        config = await update_shop_sla_config(
            db,
            current_user.shop_id,
            payload.custom_thresholds,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SlaConfigResponse(**config)


