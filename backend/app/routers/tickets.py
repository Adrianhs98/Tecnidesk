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

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ticket_evidence import EvidenceTypeEnum, TicketEvidence
from app.schemas.ticket import TicketEvidenceResponse
from app.services.storage_service import upload_evidence_image

from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from app.models.subscription import Subscription, SubscriptionStatusEnum
from app.core.dependencies import subscription_guard, get_current_user, superadmin_key_guard
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
    CycleTimeAnalyticsResponse,
)
from app.services import ticket_service
from app.services.ticket_service import (
    CustomerNotInShop,
    InvalidTechnicianRole,
    TechnicianNotInShop,
    TicketNotFound,
    UnassignedTechnicianError,
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
    response: Response,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        ticket, warning = await ticket_service.create_ticket(
            db=db,
            shop_id=current_user.shop_id,
            data=data,
        )
        if warning:
            response.headers["X-Assignment-Warning"] = warning
        return ticket
    except CustomerNotInShop as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except TechnicianNotInShop as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except InvalidTechnicianRole as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(e)
        ) from e


# ═══════════════════════════════════════════════════════════════════════════════
# 2. GET /tickets
# ═══════════════════════════════════════════════════════════════════════════════

from app.schemas.pagination import PaginatedResponse

@router.get(
    "",
    response_model=PaginatedResponse[TicketListResponse],
    summary="Listar Tickets",
    description="Obtiene los últimos tickets del taller, con filtrado opcional.",
)
async def list_tickets(
    ticket_status: TicketStatusEnum | None = Query(None, description="Filtra por estado exacto (ej. Recibido)"),
    filter_group: str | None = Query(None, description="Filtro agrupado ('activos')"),
    search: str | None = Query(None, description="Término de búsqueda general"),
    date_range: str | None = Query(None, description="Filtra por fecha, ej. 2026-01-01,2026-01-31"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200, description="Cantidad máxima a retornar (cap: 200)"),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    items, total = await ticket_service.list_tickets(
        db=db,
        shop_id=current_user.shop_id,
        skip=skip,
        limit=limit,
        status=ticket_status,
        filter_group=filter_group,
        search=search,
        date_range=date_range
    )
    return PaginatedResponse(items=items, total=total)


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
# 4. GET /tickets/analytics/cycle-times  ← DEBE ir ANTES de /{ticket_id}
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/analytics/cycle-times",
    response_model=CycleTimeAnalyticsResponse,
    summary="Métricas de Cycle Time, Lead Time y Cuellos de Botella",
    description="Calcula tiempos promedio de ciclo, lead time, desglose por etapa, cuellos de botella y tasa de cumplimiento SLA.",
)
async def get_cycle_time_analytics(
    days: int = Query(30, ge=1, le=365, description="Ventana de tiempo en días"),
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    return await ticket_service.get_workshop_cycle_time_metrics(
        db=db,
        shop_id=current_user.shop_id,
        days=days,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. GET /tickets/{ticket_id}
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
            changed_by_user_id=current_user.id,
        )
    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except UnassignedTechnicianError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
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


@router.delete(
    "/{ticket_id}/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar Ítem del Ticket",
    description="Elimina un repuesto o mano de obra, restaura el stock y recalcula el costo total.",
)
async def remove_ticket_item(
    ticket_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        await ticket_service.remove_ticket_item(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
            item_id=item_id,
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
    description="Actualiza diagnostic_notes, labor_cost y cambia automáticamente el status a ESPERANDO_APROBACION.",
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
            labor_cost=payload.labor_cost,
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
    _: str = Depends(superadmin_key_guard),
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

# ═════════════════════════════════════════════════════════════════════════════
# 11. POST /tickets/{ticket_id}/diagnose
# ═════════════════════════════════════════════════════════════════════════════
from app.schemas.diagnostic import DiagnosticResponse
from app.services.diagnostic_service import search_similar_cases
from app.services.explanation_service import ExplanationService
from app.models.diagnostic import DiagnosticQueryLog

@router.post(
    "/{ticket_id}/diagnose",
    response_model=DiagnosticResponse,
    summary="Generar diagnóstico asistido por IA",
    description="Realiza búsqueda de casos similares (RAG) y genera explicación justificada.",
)
async def diagnose_ticket(
    ticket_id: uuid.UUID,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Get ticket for context
        ticket = await ticket_service.get_ticket_by_id(
            db=db,
            ticket_id=ticket_id,
            shop_id=current_user.shop_id,
        )
        
        # Retrieval
        search_result = await search_similar_cases(
            db=db,
            shop_id=current_user.shop_id,
            device_brand=ticket.device_brand,
            device_model=ticket.device_model,
            symptom_text=ticket.issue_description,
            ticket_id=ticket_id
        )
        
        # We need the DiagnosticCase objects, not RetrievedCase
        # Wait, the prompt for build_prompt needs DiagnosticCase.
        # Let's map RetrievedCase back to a struct that ExplanationService expects.
        class SimpleCase:
            def __init__(self, id, device_brand, device_model, symptom_text, diagnosed_cause, solution_applied, source_type):
                self.id = id
                self.device_brand = device_brand
                self.device_model = device_model
                self.symptom_text = symptom_text
                self.diagnosed_cause = diagnosed_cause
                self.solution_applied = solution_applied
                self.source_type = source_type
                
        cases_for_llm = [
            SimpleCase(
                id=c.case_id,
                device_brand=c.device_brand,
                device_model=c.device_model,
                symptom_text=c.symptom_text,
                diagnosed_cause=c.diagnosed_cause,
                solution_applied=c.solution_applied,
                source_type=c.source_type
            ) for c in search_result.cases
        ]
        
        symptom_context = f"Brand: {ticket.device_brand} | Model: {ticket.device_model} | Symptom: {ticket.issue_description}"
        
        best_distance = search_result.cases[0].cosine_distance if search_result.cases else 1.0
        
        # Generation
        diagnosis = await ExplanationService.generate_explanation(
            symptom=symptom_context,
            retrieved_cases=cases_for_llm,
            best_distance=best_distance
        )
        
        # If generation failed verify, update the log that was just created
        if not diagnosis.had_sufficient_evidence and search_result.had_sufficient_evidence:
            # The search logged sufficient = True, but LLM failed to verify
            # We can update the last log for this ticket
            stmt = select(DiagnosticQueryLog).where(
                DiagnosticQueryLog.ticket_id == ticket_id
            ).order_by(DiagnosticQueryLog.created_at.desc()).limit(1)
            result = await db.execute(stmt)
            log_entry = result.scalar_one_or_none()
            if log_entry:
                log_entry.had_sufficient_evidence = False
                db.add(log_entry)
        
        await db.commit()
        return diagnosis

    except TicketNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e


# ═════════════════════════════════════════════════════════════════════════════
# 12. POST /tickets/{ticket_id}/diagnostic-chat
# ═════════════════════════════════════════════════════════════════════════════
from app.schemas.diagnostic import DiagnosticMessageIn, DiagnosticMessageResponse, ConfirmCorrectionIn, DiagnosticCaseResponse
from app.services.correction_service import CorrectionService

@router.post(
    "/{ticket_id}/diagnostic-chat",
    response_model=DiagnosticMessageResponse,
    summary="Chat con el asistente sobre el diagnóstico",
    description="Agrega un mensaje del técnico y retorna la respuesta del asistente.",
)
async def diagnostic_chat(
    ticket_id: uuid.UUID,
    payload: DiagnosticMessageIn,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        # Check ticket exists
        ticket = await ticket_service.get_ticket_by_id(
            db=db, ticket_id=ticket_id, shop_id=current_user.shop_id
        )
        return await CorrectionService.handle_chat_message(
            db=db,
            shop_id=current_user.shop_id,
            technician_id=current_user.id,
            ticket_id=ticket_id,
            message_in=payload
        )
    except TicketNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

# ═════════════════════════════════════════════════════════════════════════════
# 13. POST /tickets/{ticket_id}/diagnostic-chat/confirm
# ═════════════════════════════════════════════════════════════════════════════
@router.post(
    "/{ticket_id}/diagnostic-chat/confirm",
    response_model=DiagnosticCaseResponse,
    summary="Confirmar corrección de diagnóstico",
    description="Finaliza la conversación y guarda la causa/solución como real_validated.",
)
async def diagnostic_chat_confirm(
    ticket_id: uuid.UUID,
    payload: ConfirmCorrectionIn,
    current_user: User = Depends(subscription_guard),
    db: AsyncSession = Depends(get_db),
):
    try:
        ticket = await ticket_service.get_ticket_by_id(
            db=db, ticket_id=ticket_id, shop_id=current_user.shop_id
        )
        return await CorrectionService.confirm_correction(
            db=db,
            shop_id=current_user.shop_id,
            technician_id=current_user.id,
            ticket_id=ticket_id,
            confirm_in=payload
        )
    except TicketNotFound as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
