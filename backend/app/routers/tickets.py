"""
Router: /tickets
Endpoints para la gestión de Órdenes de Reparación (Tickets).

SEGURIDAD:
  1. Todos los endpoints están protegidos por subscription_guard.
  2. Todos inyectan `current_user.shop_id` automáticamente en los servicios.
  3. No se devuelve pin_or_password en ninguna respuesta.
"""
import time
import uuid
import magic

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket_evidence import EvidenceTypeEnum, TicketEvidence
from app.schemas.ticket import TicketEvidenceResponse
from app.services.storage_service import upload_evidence_image

from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.models.subscription import Subscription, SubscriptionStatusEnum
from app.core.dependencies import subscription_guard, get_current_user
from app.database import get_db
from app.models.ticket import TicketStatusEnum
from app.models.user import User
from app.schemas.ticket import (
    TicketAssignIn,
    TicketCreate,
    TicketDetailResponse,
    TicketDiagnosticUpdate,
    TicketItemCreate,
    TicketItemResponse,
    TicketListResponse,
    TicketResponse,
    TicketStatsResponse,
    TicketStatusUpdateIn,
    TicketUpdate,
)
from app.services import ticket_service
from app.services.ticket_service import (
    CustomerNotInShop,
    InvalidTechnicianRole,
    TechnicianNotInShop,
    TicketNotFound,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


# ═══════════════════════════════════════════════════════════════════════════════
# 1. POST /tickets
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "",
    response_model=TicketListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo Ticket",
    description="Crea una orden de reparación para un cliente del taller.",
)
async def create_ticket(
    data: TicketCreate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.create_ticket(
            db=db,
            shop_id=current_user.shop_id,
            data=data,
        )
    except CustomerNotInShop as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GET /tickets
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "",
    response_model=list[TicketListResponse],
    summary="Listar Tickets",
    description="Obtiene los últimos tickets del taller, con filtrado opcional por estado.",
)
async def list_tickets(
    ticket_status: TicketStatusEnum | None = Query(
        None, description="Filtra por estado exacto (ej. Recibido)"
    ),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima a retornar (cap: 200)"),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.list_tickets(
        db=db,
        shop_id=current_user.shop_id,
        status=ticket_status,
        limit=limit,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. GET /tickets/stats  ← DEBE ir ANTES de /{ticket_id} para que FastAPI no
#    lo interprete como un UUID
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/stats",
    response_model=TicketStatsResponse,
    summary="Estadísticas del taller",
    description="Retorna conteos reales calculados en PostgreSQL. Una sola query agregada.",
)
async def get_ticket_stats(
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.get_ticket_stats(
        db=db,
        shop_id=current_user.shop_id,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. GET /tickets/{ticket_id}
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{ticket_id}",
    response_model=TicketDetailResponse,
    summary="Detalle de un Ticket",
    description="Obtiene un ticket específico con sus ítems, cliente y técnico asignado.",
)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.get_ticket_by_id(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 4. PATCH /tickets/{ticket_id}/status
# ═══════════════════════════════════════════════════════════════════════════════

@router.patch(
    "/{ticket_id}/status",
    response_model=TicketListResponse,
    summary="Actualizar Estado",
    description="Cambia el estado de un ticket y dispara el webhook de notificación.",
)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    payload: TicketStatusUpdateIn,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.update_ticket_status(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
            new_status=payload.status,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 5. POST /tickets/{ticket_id}/items
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{ticket_id}/items",
    response_model=TicketItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir Ítem al Ticket",
    description="Agrega repuesto o mano de obra y recalcula el costo total.",
)
async def add_ticket_item(
    ticket_id: uuid.UUID,
    item_in: TicketItemCreate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.add_ticket_item(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
            data=item_in,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 6. PATCH /tickets/{ticket_id}/assign
# ═══════════════════════════════════════════════════════════════════════════════

@router.patch(
    "/{ticket_id}/assign",
    response_model=TicketResponse,
    summary="Asignar Técnico",
    description="Asigna un empleado activo y con rol suficiente al ticket.",
)
async def assign_technician(
    ticket_id: uuid.UUID,
    payload: TicketAssignIn,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.assign_technician(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
            technician_id=payload.technician_id,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except TechnicianNotInShop as e:
        # El técnico no existe en el taller, devolvemos bad request por semántica
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except InvalidTechnicianRole as e:
        # El usuario no tiene rol para ser asignado
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 7. POST /tickets/{ticket_id}/evidences
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{ticket_id}/evidences",
    response_model=TicketEvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir evidencia",
    description="Sube una foto u otro documento adjunto al ticket. Protegido multi-tenant, limita a 2MB y JPG/PNG/WEBP.",
)
async def upload_evidence(
    ticket_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    # Verificamos multi-tenant: el ticket debe pertenecer al shop del usuario
    try:
        await ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id, shop_id=current_user.shop_id)
    except TicketNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        
    content = await file.read()
    
    # Validar tamaño (2MB máximo)
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="El archivo excede el límite de 2MB permitidos."
        )
        
    # Validar MIME type real con python-magic
    try:
        mime_type = magic.from_buffer(content, mime=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se pudo determinar el tipo de archivo: {str(e)}"
        )
        
    if mime_type not in ["image/jpeg", "image/png", "image/webp"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de archivo inválido ({mime_type}). Solo imágenes JPG, PNG o WEBP son permitidas."
        )
        
    timestamp = str(int(time.time()))
    filename = file.filename or "unknown.jpg"
    
    try:
        url = await upload_evidence_image(
            file_content=content,
            shop_id=current_user.shop_id,
            ticket_id=ticket_id,
            timestamp=timestamp,
            filename=filename,
            mime_type=mime_type
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
        
    # Crear registro en la base de datos
    evidence = TicketEvidence(
        ticket_id=ticket_id,
        evidence_type=EvidenceTypeEnum.repair_photo, # Predeterminado genérico para imágenes
        file_url=url,
        file_name=filename,
        mime_type=mime_type,
        file_size=len(content)
    )
    
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    
    return evidence


# ═══════════════════════════════════════════════════════════════════════════════
# 8. GET /tickets/{ticket_id}/evidences
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{ticket_id}/evidences",
    response_model=list[TicketEvidenceResponse],
    summary="Listar evidencias",
    description="Devuelve la lista de imágenes/documentos adjuntos a un ticket. Protegido multi-tenant.",
)
async def list_evidences(
    ticket_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    # Verificamos multi-tenant
    try:
        await ticket_service.get_ticket_by_id(db=db, ticket_id=ticket_id, shop_id=current_user.shop_id)
    except TicketNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
        
    query = select(TicketEvidence).where(TicketEvidence.ticket_id == ticket_id)
    result = await db.execute(query)
    evidences = result.scalars().all()
    
    return evidences


# ═════════════════════════════════════════════════════════════════════════════
# 9. PATCH /tickets/{ticket_id}/diagnostic
# ═════════════════════════════════════════════════════════════════════════════

@router.patch(
    "/{ticket_id}/diagnostic",
    response_model=TicketResponse,
    summary="Enviar diagnóstico y presupuesto",
    description="Actualiza diagnostic_notes, total_cost y cambia automáticamente el status a ESPERANDO_APROBACION.",
)
async def update_diagnostic(
    ticket_id: uuid.UUID,
    payload: TicketDiagnosticUpdate,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await ticket_service.update_ticket_diagnostic(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
            diagnostic_notes=payload.diagnostic_notes,
            total_cost=payload.total_cost,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═════════════════════════════════════════════════════════════════════════════
# 10. POST /admin/activate-shop
# ═════════════════════════════════════════════════════════════════════════════

class ActivateShopIn(BaseModel):
    shop_id: uuid.UUID
    days: int = 365

@router.post(
    "/admin/activate-shop",
    summary="Activar Shop Manualmente",
)
async def activate_shop(
    payload: ActivateShopIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Subscription).where(Subscription.shop_id == payload.shop_id).order_by(Subscription.started_at.desc())
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    ends_at = datetime.now(timezone.utc) + timedelta(days=payload.days)
    subscription.status = SubscriptionStatusEnum.active
    subscription.ends_at = ends_at
    
    await db.commit()
    
    return {
        "message": "Shop activado",
        "shop_id": payload.shop_id,
        "ends_at": ends_at
    }
