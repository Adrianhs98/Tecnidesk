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


@router.get("/metrics", response_model=TechnicianMetricsTable)
async def get_metrics(
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    """
    Obtiene las métricas de todos los técnicos del taller, 
    incluyendo especialidades inferidas y totales.
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
