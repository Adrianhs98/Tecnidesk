"""
Router para la gestión de Técnicos.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import admin_guard, subscription_guard
from app.database import get_db
from app.models.user import User
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianAccessCreate,
    TechnicianMeResponse,
    TechnicianMetricsTable,
    TechnicianResponse,
    TechnicianUpdate,
)
from app.services import technician_service

router = APIRouter(
    prefix="/technicians",
    tags=["Technicians"],
    responses={
        401: {"description": "No autenticado"},
        402: {"description": "Suscripción inactiva o expirada"},
        403: {"description": "No tiene permisos de administrador"},
    },
)


@router.get("", response_model=list[TechnicianResponse])
async def list_technicians(
    include_inactive: bool = False,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Lista los técnicos del taller. Protegido por suscripción."""
    return await technician_service.get_technicians(db, current_user.shop_id, include_inactive)


@router.get("/me", response_model=TechnicianMeResponse)
async def get_technician_me(
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene el perfil operativo del técnico autenticado con sus estadísticas
    (tickets activos, tickets completados y especialidades) sin exponer datos financieros.
    """
    return await technician_service.get_technician_me(db, current_user, current_user.shop_id)


@router.post("", response_model=TechnicianResponse, status_code=status.HTTP_201_CREATED)
async def create_technician(
    data: TechnicianCreate,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo técnico. Solo administradores."""
    try:
        return await technician_service.create_technician(db, current_user.shop_id, data)
    except technician_service.TechnicianDuplicate as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        if "Fallo al enviar correo" in str(e):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
        raise


@router.get("/metrics", response_model=TechnicianMetricsTable)
async def get_metrics(
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene las métricas de todos los técnicos del taller, 
    incluyendo especialidades inferidas y totales financieros. Solo administradores.
    """
    return await technician_service.get_technician_metrics(db, current_user.shop_id)


@router.get("/{id}", response_model=TechnicianResponse)
async def get_technician(
    id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """Detalle de un técnico."""
    tech = await technician_service.get_technician_by_id(db, id, current_user.shop_id)
    if not tech:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnico no encontrado.")
    return tech


@router.post("/{id}/access", response_model=TechnicianResponse)
async def generate_technician_access(
    id: uuid.UUID,
    data: TechnicianAccessCreate,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """Genera acceso al sistema para un técnico existente. Solo administradores."""
    tech = await technician_service.get_technician_by_id(db, id, current_user.shop_id)
    if not tech:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Técnico no encontrado.")
    if not tech.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se puede generar acceso a un técnico inactivo.")
    if tech.user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El técnico ya tiene acceso al sistema.")

    try:
        await technician_service.grant_technician_access(db, current_user.shop_id, tech, str(data.email))
        await db.commit()
        await db.refresh(tech)
        return tech
    except technician_service.TechnicianDuplicate as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        await db.rollback()
        if "Fallo al enviar correo" in str(e):
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))
        raise


@router.patch("/{id}", response_model=TechnicianResponse)
async def update_technician(
    id: uuid.UUID,
    data: TechnicianUpdate,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza datos básicos de un técnico. Solo administradores."""
    try:
        return await technician_service.update_technician(db, id, current_user.shop_id, data)
    except technician_service.TechnicianNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except technician_service.TechnicianDuplicate as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.delete("/{id}", response_model=TechnicianResponse)
async def deactivate_technician(
    id: uuid.UUID,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """Da de baja lógica a un técnico (is_active = False). Solo administradores."""
    try:
        return await technician_service.deactivate_technician(db, id, current_user.shop_id)
    except technician_service.TechnicianNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/reactivate", response_model=TechnicianResponse)
async def reactivate_technician(
    id: uuid.UUID,
    current_user: User = Depends(admin_guard),
    db: AsyncSession = Depends(get_db),
):
    """Reactiva un técnico dado de baja (is_active = True). Solo administradores."""
    try:
        return await technician_service.reactivate_technician(db, id, current_user.shop_id)
    except technician_service.TechnicianNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
