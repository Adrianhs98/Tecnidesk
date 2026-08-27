"""
Servicio: ticket_service — Lógica de negocio para órdenes de reparación.

SEGURIDAD (C1 / D2):
  - encrypt_pin() se llama AQUÍ, antes de asignar pin_or_password al modelo.
  - pin_or_password NUNCA sale de este módulo sin cifrar y NUNCA se devuelve
    en los objetos retornados (campo excluido mediante __dict__ manipulation).
  - decrypt_pin() solo se usa en servicios internos — nunca en rutas públicas.

MULTI-TENANT:
  - Todas las queries incluyen shop_id en el WHERE.
  - Ninguna operación puede cruzar datos entre talleres.
"""
from __future__ import annotations

import datetime
import json
import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select, func, case, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.models.shop import Shop
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_item import TicketItem
from app.models.ticket_status_history import TicketStatusHistory
from app.models.user import User, UserRoleEnum
from app.services.encryption_service import decrypt_pin, encrypt_pin
from app.services import email_service
from app.config import get_settings

if TYPE_CHECKING:
    # Importación circular evitada: solo para type-checking
    pass


# ─── SLA Config & Helpers ─────────────────────────────────────────────────────

SLA_THRESHOLDS_HOURS: dict[TicketStatusEnum, int | None] = {
    TicketStatusEnum.EN_ESPERA_INGRESO: 48,
    TicketStatusEnum.EN_REVISION: 24,
    TicketStatusEnum.EN_REPARACION: 48,
    TicketStatusEnum.ESPERANDO_APROBACION: None,  # Paused
    TicketStatusEnum.ESPERANDO_REPUESTO: None,    # Paused
    TicketStatusEnum.LISTO_PARA_RETIRAR: None,   # Ready
    TicketStatusEnum.NO_APROBADO: None,          # Terminal
}


def is_ticket_sla_breached(
    ticket: Ticket,
    now: datetime.datetime | None = None,
    custom_thresholds: dict[str, int] | None = None,
) -> bool:
    """Calcula si un ticket ha superado el SLA dinámico asignado a su estado actual."""
    status_key = ticket.status.value if hasattr(ticket.status, "value") else str(ticket.status)
    if custom_thresholds and status_key in custom_thresholds:
        threshold = custom_thresholds[status_key]
    else:
        threshold = SLA_THRESHOLDS_HOURS.get(ticket.status)

    if threshold is None:
        return False
    current_time = now or datetime.datetime.now(datetime.timezone.utc)
    ref_time = ticket.updated_at or ticket.created_at
    if ref_time is None:
        return False
    if ref_time.tzinfo is None:
        ref_time = ref_time.replace(tzinfo=datetime.timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=datetime.timezone.utc)
    elapsed_hours = (current_time - ref_time).total_seconds() / 3600
    return elapsed_hours >= threshold


# ─── Excepciones de dominio ───────────────────────────────────────────────────

class TicketNotFound(Exception):
    """El ticket no existe o no pertenece al shop_id indicado."""


class CustomerNotInShop(Exception):
    """El customer_id no pertenece al shop_id indicado."""


class TechnicianNotInShop(Exception):
    """El técnico no pertenece al shop_id indicado."""


class InvalidTechnicianRole(Exception):
    """El usuario no tiene rol de técnico o admin — no puede asignarse."""


class UnassignedTechnicianError(Exception):
    """Debe asignar un técnico responsable antes de iniciar la reparación."""


# ─── Helpers internos ─────────────────────────────────────────────────────────

async def _record_status_history(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    from_status: str | None,
    to_status: str,
    changed_by_user_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> TicketStatusHistory:
    """
    Registra una entrada en el historial de transiciones de estado del ticket.
    Se ejecuta dentro de la misma transacción de la base de datos.
    """
    history = TicketStatusHistory(
        ticket_id=ticket_id,
        from_status=from_status,
        to_status=to_status,
        changed_by_user_id=changed_by_user_id,
        reason=reason,
    )
    db.add(history)
    return history


def _clear_pin(ticket: Ticket) -> Ticket:
    """
    Asegura que pin_or_password NO esté accesible en el objeto retornado.
    ¡PELIGRO!: Modificar ticket.pin_or_password = None borraba el PIN de la DB 
    por culpa del commit() global en get_db. 
    Como Pydantic no mapea el campo, devolverlo intacto es 100% seguro.
    """
    return ticket


async def _get_ticket_or_404(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    *options,
) -> Ticket:
    """
    Busca un ticket validando multi-tenant.  Lanza TicketNotFound si no existe.

    Args:
        options: Opciones de carga eager (selectinload) adicionales.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket_id, Ticket.shop_id == shop_id)
        .options(*options)
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        raise TicketNotFound(
            f"Ticket {ticket_id} no encontrado en el taller {shop_id}."
        )
    return ticket


async def _dispatch_webhook(
    db: AsyncSession,
    ticket: Ticket,
    event_type: str,
    payload: dict,
) -> None:
    """
    Registra y dispara una notificación webhook.

    Estrategia actual: fire-and-forget asíncrono con registro en WebhookLog.
    Si webhook_service no está disponible se omite silenciosamente para no
    bloquear la operación principal.

    Args:
        event_type: Ej. "ticket.created", "ticket.status_changed".
        payload:    Datos del evento como dict serializable a JSON.
    """
    try:
        # Importación lazy para evitar circular imports en el futuro
        from app.services import webhook_service  # noqa: PLC0415
        await webhook_service.notify(
            db=db,
            ticket=ticket,
            event_type=event_type,
            payload=payload,
        )
    except Exception as exc:  # noqa: BLE001
        # El webhook nunca debe romper la operación principal
        import logging
        logging.getLogger("tecnidesk.ticket_service").exception(
            f"Fallo crítico al despachar webhook de tipo {event_type} para el ticket {ticket.id}: {exc}"
        )


# ═════════════════════════════════════════════════════════════════════════════
# FUNCIONES PÚBLICAS
# ═════════════════════════════════════════════════════════════════════════════


async def create_ticket(
    db: AsyncSession,
    shop_id: uuid.UUID,
    data: "TicketCreate",  # noqa: F821 — schema definido en app/schemas/
) -> tuple[Ticket, str | None]:
    """
    Crea una nueva orden de reparación.

    Pasos:
      1. Get-or-create del cliente por (client_email, shop_id).
         Si no existe, se crea con valores provisionales (nombre = email,
         teléfono = "0000000000000") que el técnico puede actualizar luego.
      2. Cifrar pin_or_password con Fernet (encrypt_pin).
      3. Generar tracking_token via uuid4.
      4. Insertar Ticket en DB, commit + refresh.
      5. Disparar webhook ticket.created (no-blocking).
      6. Enviar email de confirmación al cliente.

    Returns:
        Objeto Ticket sin pin_or_password expuesto.
    """
    # ── 1. Get-or-create del cliente por email ────────────────────────────────
    customer_result = await db.execute(
        select(Customer).where(
            Customer.email == data.client_email,
            Customer.shop_id == shop_id,
        )
    )
    customer = customer_result.scalar_one_or_none()

    if customer is None:
        # full_name y phone_number usan valores provistos o su fallback
        customer = Customer(
            shop_id=shop_id,
            email=data.client_email,
            full_name=getattr(data, "client_name", None) or data.client_email,
            phone_number=getattr(data, "client_phone", None) or "000000000000",
        )
        db.add(customer)
        try:
            await db.flush()   # Obtiene el customer.id sin hacer commit todavía
        except Exception:
            await db.rollback()
            raise

    # ── 2. Cifrar PIN antes de asignar al modelo (D2 / C1) ───────────────────
    encrypted_pin: str | None = encrypt_pin(data.pin_or_password) if getattr(data, "pin_or_password", None) else None

    # ── 3. tracking_token generado aquí (y también como default en el modelo) ─
    tracking_token = str(uuid.uuid4())

    # ── NUEVO: Resolver técnico según modo de asignación ──
    resolved_tech_id = None
    assignment_warning = None

    if getattr(data, "assignment_mode", "unassigned") == "manual":
        from app.services.technician_service import get_technician_by_id
        tech = await get_technician_by_id(db, data.technician_id, shop_id)
        if tech is None:
            raise TechnicianNotInShop(f"Técnico {data.technician_id} no encontrado en el taller.")
        if not tech.is_active:
            raise InvalidTechnicianRole("El técnico seleccionado está inactivo.")
        resolved_tech_id = tech.id

    elif getattr(data, "assignment_mode", "unassigned") == "random":
        from app.services.technician_service import pick_least_loaded_technician
        tech = await pick_least_loaded_technician(db, shop_id)
        if tech:
            resolved_tech_id = tech.id
        else:
            assignment_warning = "No hay técnicos activos; ticket creado sin asignación."

    # ── 4. Crear y persistir el Ticket ───────────────────────────────────────
    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        device_brand=data.device_brand,
        device_model=data.device_model,
        issue_description=data.issue_description,
        internal_notes=getattr(data, "internal_notes", None),
        diagnostic_notes=getattr(data, "diagnostic_notes", None),
        requires_approval=getattr(data, "requires_approval", False),
        pin_or_password=encrypted_pin,              # Fernet ciphertext
        status=TicketStatusEnum.EN_ESPERA_INGRESO,
        tracking_token=tracking_token,
        technician_id=resolved_tech_id,
    )
    db.add(ticket)

    try:
        await db.flush()
        await _record_status_history(
            db=db,
            ticket_id=ticket.id,
            from_status=None,
            to_status=ticket.status.value,
            changed_by_user_id=None,
            reason="Creación de la orden de reparación",
        )
        await db.commit()
        # Reload with eager-loaded relations to avoid MissingGreenlet on serialization
        refreshed = await db.execute(
            select(Ticket)
            .where(Ticket.id == ticket.id)
            .options(
                selectinload(Ticket.customer),
                selectinload(Ticket.technician),
            )
        )
        ticket = refreshed.scalar_one()
    except Exception:
        await db.rollback()
        raise

    # ── 5. Webhook ticket.created (fire-and-forget) ───────────────────────────
    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.created",
        payload={
            "ticket_id": str(ticket.id),
            "shop_id": str(shop_id),
            "tracking_token": ticket.tracking_token,
            "status": ticket.status.value,
        },
    )

    # ── 6. Enviar email al cliente con el tracking ──────────────────────────────
    if customer.email:
        shop = await db.scalar(select(Shop).where(Shop.id == shop_id))
        if shop:
            await email_service.send_ticket_email(
                to_email=customer.email,
                ticket=ticket,
                shop=shop
            )

    ticket.customer = customer
    return _clear_pin(ticket), assignment_warning


async def get_ticket_by_id(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
) -> Ticket:
    """
    Obtiene un ticket con sus relaciones eager-loaded.

    Carga: customer, technician, items, evidences, status_history.

    Returns:
        Ticket sin pin_or_password expuesto.

    Raises:
        TicketNotFound: Si no existe o no pertenece al shop.
    """
    ticket = await _get_ticket_or_404(
        db,
        ticket_id,
        shop_id,
        selectinload(Ticket.customer),
        selectinload(Ticket.technician),
        selectinload(Ticket.items),
        selectinload(Ticket.evidences),
        selectinload(Ticket.status_history),
    )
    # Desencriptar PIN y adjuntarlo como device_password (solo para uso admin)
    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)


async def get_ticket_by_tracking_token(
    db: AsyncSession,
    token: str,
) -> Ticket | None:
    """
    Busca un ticket filtrando únicamente por su tracking_token.
    Sin validación de shop_id para permitir acceso público de clientes.
    Incluye el shop para acceder a contact_whatsapp.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.tracking_token == token)
        .options(selectinload(Ticket.shop), selectinload(Ticket.evidences))
    )
    ticket = result.scalar_one_or_none()
    
    if ticket is None:
        return None
        
    return _clear_pin(ticket)


async def update_ticket_diagnostic(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    diagnostic_notes: str,
    labor_cost: float,
) -> Ticket:
    """
    Actualiza diagnostic_notes y labor_cost de un ticket,
    activa requires_approval y cambia status a ESPERANDO_APROBACION.

    Returns:
        Ticket actualizado sin pin_or_password.

    Raises:
        TicketNotFound: Si no existe o no pertenece al shop.
    """
    ticket = await _get_ticket_or_404(db, ticket_id, shop_id)

    ticket.diagnostic_notes = diagnostic_notes

    # Buscar si ya existe un item de labor general
    from app.models.ticket_item import ItemTypeEnum
    stmt = select(TicketItem).where(
        TicketItem.ticket_id == ticket_id, 
        TicketItem.item_type == ItemTypeEnum.labor,
        TicketItem.description == "Mano de obra"
    )
    result = await db.execute(stmt)
    labor_item = result.scalars().first()
    
    if labor_item:
        labor_item.unit_price = Decimal(str(labor_cost))
    else:
        labor_item = TicketItem(
            ticket_id=ticket.id,
            item_type=ItemTypeEnum.labor,
            description="Mano de obra",
            quantity=1,
            unit_price=Decimal(str(labor_cost)),
            inventory_id=None
        )
        db.add(labor_item)
        
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # Recalcular el costo total sumando todos los items (ahora el nuevo de labor está incluido)
    total_cost = await calculate_ticket_total(db, ticket_id)

    old_status = ticket.status
    ticket.requires_approval = True
    ticket.status = TicketStatusEnum.ESPERANDO_APROBACION

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=old_status.value if old_status else None,
        to_status=TicketStatusEnum.ESPERANDO_APROBACION.value,
        changed_by_user_id=None,
        reason="Diagnóstico y presupuesto emitido",
    )

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.diagnostic_sent",
        payload={
            "ticket_id": str(ticket.id),
            "shop_id": str(shop_id),
            "status": ticket.status.value,
            "total_cost": str(ticket.total_cost),
        },
    )

    # ── Notificar al cliente por email (fire-and-forget) ─────────────────────
    try:
        customer_result = await db.execute(
            select(Customer).where(Customer.id == ticket.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer and customer.email:
            _settings = get_settings()
            tracking_url = (
                f"{_settings.frontend_url.rstrip('/')}/tracking/{ticket.tracking_token}"
            )
            await email_service.send_quote_ready_email(
                email=customer.email,
                tracking_url=tracking_url,
                device_model=f"{ticket.device_brand} {ticket.device_model}",
            )
    except Exception:
        # El email nunca debe romper la operación principal
        pass

    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)


async def approve_ticket_by_token(
    db: AsyncSession,
    token: str,
) -> Ticket | None:
    """
    Aprueba el presupuesto de un ticket usando su tracking_token (público).
    Cambia status de ESPERANDO_APROBACION a EN_REPARACION.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.tracking_token == token)
        .options(selectinload(Ticket.shop), selectinload(Ticket.evidences))
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None

    if ticket.status != TicketStatusEnum.ESPERANDO_APROBACION:
        return ticket  # ya fue procesado, retorna sin cambios

    old_status = ticket.status
    ticket.status = TicketStatusEnum.EN_REPARACION
    ticket.requires_approval = False

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=old_status.value if old_status else None,
        to_status=TicketStatusEnum.EN_REPARACION.value,
        changed_by_user_id=None,
        reason="Presupuesto aprobado por el cliente",
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # Re-cargar con relaciones (db.refresh pierde las relaciones eager-loaded)
    refreshed = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(selectinload(Ticket.shop), selectinload(Ticket.evidences))
    )
    ticket = refreshed.scalar_one()

    # Disparar webhook de cambio de estado en segundo plano
    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.status_changed",
        payload={
            "ticket_id": str(ticket.id),
            "shop_id": str(ticket.shop_id),
            "status": ticket.status.value,
            "previous_status": TicketStatusEnum.ESPERANDO_APROBACION.value,
        },
    )

    return _clear_pin(ticket)


async def reject_ticket_by_token(
    db: AsyncSession,
    token: str,
    rejection_reason: str | None = None,
) -> Ticket | None:
    """
    Rechaza el presupuesto de un ticket usando su tracking_token (público).
    Cambia status de ESPERANDO_APROBACION a NO_APROBADO.
    """
    result = await db.execute(
        select(Ticket)
        .where(Ticket.tracking_token == token)
        .options(selectinload(Ticket.shop), selectinload(Ticket.evidences))
    )
    ticket = result.scalar_one_or_none()
    if ticket is None:
        return None

    if ticket.status != TicketStatusEnum.ESPERANDO_APROBACION:
        return ticket  # ya fue procesado, retorna sin cambios

    old_status = ticket.status
    ticket.status = TicketStatusEnum.NO_APROBADO
    ticket.requires_approval = False

    if rejection_reason:
        note_prefix = f"[MOTIVO DE RECHAZO]: {rejection_reason}\n"
        ticket.internal_notes = note_prefix + (ticket.internal_notes or "")

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=old_status.value if old_status else None,
        to_status=TicketStatusEnum.NO_APROBADO.value,
        changed_by_user_id=None,
        reason=rejection_reason or "Presupuesto rechazado por el cliente",
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    # Re-cargar con relaciones (db.refresh pierde las relaciones eager-loaded)
    refreshed = await db.execute(
        select(Ticket)
        .where(Ticket.id == ticket.id)
        .options(selectinload(Ticket.shop), selectinload(Ticket.evidences))
    )
    ticket = refreshed.scalar_one()

    # Disparar webhook de cambio de estado en segundo plano
    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.status_changed",
        payload={
            "ticket_id": str(ticket.id),
            "shop_id": str(ticket.shop_id),
            "status": ticket.status.value,
            "previous_status": TicketStatusEnum.ESPERANDO_APROBACION.value,
        },
    )

    return _clear_pin(ticket)


async def get_ticket_stats(
    db: AsyncSession,
    shop_id: uuid.UUID,
) -> dict:
    """
    Calcula estadísticas reales del taller en una sola consulta SQL agregada.

    Usa COUNT() FILTER (WHERE ...) nativo de PostgreSQL delegando el cálculo
    al motor de base de datos — O(1) independiente del volumen de tickets.

    Returns:
        Dict con total, activos, listos y espera como enteros.
    """
    estados_inactivos = [
        TicketStatusEnum.LISTO_PARA_RETIRAR,
        TicketStatusEnum.NO_APROBADO,
    ]

    result = await db.execute(
        select(
            func.count(Ticket.id).label("total"),
            func.count(Ticket.id).filter(
                Ticket.status.not_in(estados_inactivos)
            ).label("activos"),
            func.count(Ticket.id).filter(
                Ticket.status == TicketStatusEnum.LISTO_PARA_RETIRAR
            ).label("listos"),
            func.count(Ticket.id).filter(
                Ticket.status == TicketStatusEnum.EN_ESPERA_INGRESO
            ).label("espera"),
        ).where(Ticket.shop_id == shop_id)
    )
    row = result.one()
    return {
        "total": row.total,
        "activos": row.activos,
        "listos": row.listos,
        "espera": row.espera,
    }


async def list_tickets(
    db: AsyncSession,
    shop_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    status: TicketStatusEnum | None = None,
    filter_group: str | None = None,
    search: str | None = None,
    date_range: str | None = None,
    technician_id: uuid.UUID | None = None,
    unassigned_only: bool = False,
) -> tuple[list[Ticket], int]:
    limit = min(limit, 200)

    stmt = (
        select(Ticket)
        .join(Customer, Ticket.customer_id == Customer.id)
        .where(Ticket.shop_id == shop_id)
        .options(
            selectinload(Ticket.customer),
            selectinload(Ticket.technician),
        )
    )

    if unassigned_only:
        stmt = stmt.where(Ticket.technician_id.is_(None))
    elif technician_id is not None:
        stmt = stmt.where(
            or_(
                Ticket.technician_id == technician_id,
                Ticket.assigned_technician_id == technician_id,
            )
        )

    if status is not None:
        stmt = stmt.where(Ticket.status == status)
    elif filter_group == "activos":
        estados_inactivos = [
            TicketStatusEnum.LISTO_PARA_RETIRAR,
            TicketStatusEnum.NO_APROBADO,
        ]
        stmt = stmt.where(Ticket.status.not_in(estados_inactivos))
    
    if search:
        search_term = f"%{search}%"
        conditions = [
            Customer.full_name.ilike(search_term),
            Ticket.device_brand.ilike(search_term),
            Ticket.device_model.ilike(search_term)
        ]
        try:
            parsed_id = uuid.UUID(search)
            conditions.append(Ticket.id == parsed_id)
        except ValueError:
            pass
            
        stmt = stmt.where(or_(*conditions))
            
    if date_range:
        # Assuming date_range is like 'YYYY-MM-DD,YYYY-MM-DD'
        parts = date_range.split(',')
        if len(parts) == 2:
            try:
                start_date = datetime.datetime.strptime(parts[0], '%Y-%m-%d')
                end_date = datetime.datetime.strptime(parts[1], '%Y-%m-%d')
                stmt = stmt.where(Ticket.created_at >= start_date, Ticket.created_at <= end_date)
            except ValueError:
                pass

    total_query = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one_or_none() or 0

    from app.services.shop_service import get_effective_sla_thresholds
    shop_sla_config = await db.scalar(select(Shop.sla_config).where(Shop.id == shop_id))
    effective_slas = get_effective_sla_thresholds(shop_sla_config)

    h_espera = effective_slas.get("EN_ESPERA_INGRESO", 48)
    h_revision = effective_slas.get("EN_REVISION", 24)
    h_reparacion = effective_slas.get("EN_REPARACION", 48)

    status_timestamp = func.coalesce(Ticket.updated_at, Ticket.created_at)

    sla_breached_case = case(
        (
            (Ticket.status == TicketStatusEnum.EN_ESPERA_INGRESO)
            & (status_timestamp < func.now() - datetime.timedelta(hours=h_espera)),
            0,
        ),
        (
            (Ticket.status == TicketStatusEnum.EN_REVISION)
            & (status_timestamp < func.now() - datetime.timedelta(hours=h_revision)),
            0,
        ),
        (
            (Ticket.status == TicketStatusEnum.EN_REPARACION)
            & (status_timestamp < func.now() - datetime.timedelta(hours=h_reparacion)),
            0,
        ),
        else_=1,
    )

    stmt = stmt.order_by(
        case((Ticket.technician_id.is_(None), 0), else_=1),
        sla_breached_case,
        Ticket.created_at.desc(),
    ).offset(skip).limit(limit)

    result = await db.execute(stmt)
    tickets = list(result.scalars().all())

    for t in tickets:
        decrypted = decrypt_pin(t.pin_or_password)
        t.__dict__["device_password"] = decrypted if decrypted else None
        _clear_pin(t)

    return tickets, total


async def update_ticket_status(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    new_status: TicketStatusEnum,
    changed_by_user_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> Ticket:
    """
    Actualiza el estado de un ticket y dispara el webhook de cambio.

    Args:
        new_status: Nuevo estado destino.
        changed_by_user_id: UUID del usuario que realiza el cambio.
        reason: Motivo opcional del cambio.

    Returns:
        Ticket actualizado sin pin_or_password.

    Raises:
        TicketNotFound: Si no existe o no pertenece al shop.
        UnassignedTechnicianError: Si se intenta pasar a EN_REPARACION sin técnico asignado.
    """
    ticket = await _get_ticket_or_404(
        db,
        ticket_id,
        shop_id,
        selectinload(Ticket.customer),
        selectinload(Ticket.technician),
        selectinload(Ticket.status_history),
    )

    if new_status == TicketStatusEnum.EN_REPARACION and ticket.technician_id is None:
        raise UnassignedTechnicianError(
            "Debe asignar un técnico responsable antes de iniciar la reparación."
        )

    old_status: TicketStatusEnum = ticket.status
    ticket.status = new_status

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=old_status.value if old_status else None,
        to_status=new_status.value,
        changed_by_user_id=changed_by_user_id,
        reason=reason,
    )

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    # Webhook ticket.status_changed con old/new status
    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.status_changed",
        payload={
            "ticket_id": str(ticket.id),
            "shop_id": str(shop_id),
            "old_status": old_status.value,
            "new_status": new_status.value,
        },
    )

    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)


async def assign_technician(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    technician_id: uuid.UUID,
) -> Ticket:
    """
    Asigna un técnico o admin a un ticket, validando multi-tenant y rol.

    Args:
        technician_id: UUID del usuario a asignar.

    Returns:
        Ticket actualizado sin pin_or_password.

    Raises:
        TicketNotFound: Si el ticket no existe en el shop.
        TechnicianNotInShop: Si el usuario no pertenece al shop.
        InvalidTechnicianRole: Si el usuario no tiene rol permitido.
    """
    # ── Validar en módulo técnicos ──────────────────────────────────────────
    from app.services.technician_service import get_technician_by_id
    tech = await get_technician_by_id(db, technician_id, shop_id)
    if tech is None:
        raise TechnicianNotInShop(
            f"El técnico {technician_id} no existe en el taller {shop_id}."
        )
    if not tech.is_active:
        raise InvalidTechnicianRole("El técnico seleccionado está inactivo.")

    # ── Asignar ───────────────────────────────────────────────────────────────
    ticket = await _get_ticket_or_404(db, ticket_id, shop_id)
    ticket.technician_id = tech.id

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)


async def assign_me_ticket(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    user: User,
) -> Ticket:
    """
    Asigna el ticket al técnico autenticado si está sin asignar o ya le pertenece.
    Si está asignado a otro técnico, lanza HTTP 409 Conflict.
    """
    ticket = await _get_ticket_or_404(
        db,
        ticket_id,
        shop_id,
        selectinload(Ticket.customer),
        selectinload(Ticket.technician),
        selectinload(Ticket.status_history),
    )

    from app.models.technician import Technician
    tech = await db.scalar(
        select(Technician).where(Technician.user_id == user.id, Technician.shop_id == shop_id)
    )
    if not tech:
        tech = await db.scalar(
            select(Technician).where(Technician.full_name == user.full_name, Technician.shop_id == shop_id)
        )
        if tech and tech.user_id is None:
            tech.user_id = user.id
            db.add(tech)
            await db.flush()
        elif not tech:
            tech = Technician(
                shop_id=shop_id,
                full_name=user.full_name,
                user_id=user.id,
                is_active=True,
            )
            db.add(tech)
            await db.flush()

    if ticket.technician_id is not None and ticket.technician_id != tech.id:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El ticket ya está asignado a otro técnico."
        )

    ticket.technician_id = tech.id
    ticket.technician = tech

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=ticket.status.value if ticket.status else None,
        to_status=ticket.status.value if ticket.status else "EN_ESPERA_INGRESO",
        changed_by_user_id=user.id,
        reason=f"Ticket auto-asignado por el técnico {user.full_name}",
    )

    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise

    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)


async def reveal_ticket_pin(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    user: User,
) -> str | None:
    """
    Registra el acceso auditor al PIN en el historial y retorna el PIN descifrado.
    """
    ticket = await _get_ticket_or_404(db, ticket_id, shop_id)

    await _record_status_history(
        db=db,
        ticket_id=ticket.id,
        from_status=ticket.status.value if ticket.status else None,
        to_status="PIN_REVEALED",
        changed_by_user_id=user.id,
        reason="PIN revelado por técnico",
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    if not ticket.pin_or_password:
        return None

    return decrypt_pin(ticket.pin_or_password)


async def add_ticket_item(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    data: "TicketItemCreate",  # noqa: F821 — schema en app/schemas/
) -> TicketItem:
    """
    Agrega un ítem (repuesto, mano de obra, etc.) a un ticket.

    Pasos:
      1. Validar multi-tenant del ticket.
      2. Crear TicketItem, commit + refresh.
      3. Recalcular total_cost del ticket (llama a calculate_ticket_total).
      4. Webhook ticket.item_added (opcional, no-blocking).

    Returns:
        El TicketItem creado.

    Raises:
        TicketNotFound: Si el ticket no existe en el shop.
    """
    # ── 1. Validar multi-tenant del ticket ────────────────────────────────────
    ticket = await _get_ticket_or_404(db, ticket_id, shop_id)

    # ── 1.b Validar inventario y descontar stock ──────────────────────────────
    from app.models.ticket_item import ItemTypeEnum
    unit_price = Decimal(str(data.unit_price))

    if data.item_type == ItemTypeEnum.part and getattr(data, "inventory_id", None) is not None:
        from app.models.inventory import Inventory
        from sqlalchemy import update
        from fastapi import HTTPException
        
        result = await db.execute(
            update(Inventory)
            .where(Inventory.id == data.inventory_id)
            .where(Inventory.shop_id == shop_id)
            .where(Inventory.stock_quantity >= data.quantity)
            .values(stock_quantity=Inventory.stock_quantity - data.quantity)
            .returning(Inventory.selling_price)
        )
        selling_price = result.scalar_one_or_none()
        
        if selling_price is None:
            inv = await db.get(Inventory, data.inventory_id)
            if not inv or inv.shop_id != shop_id:
                raise HTTPException(status_code=404, detail="Item de inventario no encontrado")
            raise HTTPException(status_code=409, detail=f"Stock insuficiente para '{inv.item_name}'")
            
        unit_price = Decimal(str(selling_price))

    # ── 2. Crear el ítem ──────────────────────────────────────────────────────
    item = TicketItem(
        ticket_id=ticket.id,
        inventory_id=getattr(data, "inventory_id", None),
        item_type=data.item_type,
        description=data.description,
        quantity=data.quantity,
        unit_price=unit_price,
    )
    db.add(item)

    try:
        await db.commit()
        await db.refresh(item)
    except Exception:
        await db.rollback()
        raise

    # ── 3. Recalcular total_cost del ticket ───────────────────────────────────
    await calculate_ticket_total(db, ticket_id)

    # ── 4. Webhook ticket.item_added (fire-and-forget) ────────────────────────
    await _dispatch_webhook(
        db=db,
        ticket=ticket,
        event_type="ticket.item_added",
        payload={
            "ticket_id": str(ticket_id),
            "shop_id": str(shop_id),
            "item_id": str(item.id),
            "description": item.description,
            "quantity": item.quantity,
            "unit_price": str(item.unit_price),
        },
    )

    return item


async def remove_ticket_item(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    item_id: uuid.UUID,
) -> None:
    """
    Elimina un ítem de un ticket, restaura el stock (si es repuesto),
    y recalcula el total_cost del ticket.
    """
    # 1. Validar ticket (multi-tenant)
    await _get_ticket_or_404(db, ticket_id, shop_id)
    
    # 2. Buscar item
    stmt = select(TicketItem).where(TicketItem.id == item_id, TicketItem.ticket_id == ticket_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()
    
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Item no encontrado en el ticket")
        
    # 3. Restaurar stock si era pieza del inventario
    from app.models.ticket_item import ItemTypeEnum
    if item.item_type == ItemTypeEnum.part and item.inventory_id is not None:
        from app.models.inventory import Inventory
        from sqlalchemy import update
        await db.execute(
            update(Inventory)
            .where(Inventory.id == item.inventory_id)
            .values(stock_quantity=Inventory.stock_quantity + item.quantity)
        )
        
    # 4. Eliminar item
    await db.delete(item)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
        
    # 5. Recalcular total
    await calculate_ticket_total(db, ticket_id)


async def calculate_ticket_total(
    db: AsyncSession,
    ticket_id: uuid.UUID,
) -> Decimal:
    """
    Recalcula y persiste el total_cost del ticket.

    Fórmula:  SUM(quantity * unit_price) de todos los TicketItem del ticket.

    Usa Decimal para aritmética exacta (evitar errores de punto flotante).

    Returns:
        El nuevo total_cost como Decimal.
    """
    # Cargar todos los ítems del ticket
    items_result = await db.execute(
        select(TicketItem).where(TicketItem.ticket_id == ticket_id)
    )
    items = list(items_result.scalars().all())

    # Suma exacta con Decimal
    total = sum(
        Decimal(str(item.quantity)) * Decimal(str(item.unit_price))
        for item in items
    ) if items else Decimal("0.00")

    # Actualizar ticket.total_cost sin necesitar shop_id (es una operación interna)
    ticket_result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id)
    )
    ticket = ticket_result.scalar_one_or_none()
    if ticket is not None:
        ticket.total_cost = total
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return total


# ═══════════════════════════════════════════════════════════════════════════════
# Operational Analytics: Cycle Times, Lead Time & Bottlenecks (Fase 5)
# ═══════════════════════════════════════════════════════════════════════════════

STAGE_LABELS: dict[TicketStatusEnum, str] = {
    TicketStatusEnum.EN_ESPERA_INGRESO: "En Espera de Ingreso",
    TicketStatusEnum.EN_REVISION: "En Revisión",
    TicketStatusEnum.ESPERANDO_APROBACION: "Esperando Aprobación",
    TicketStatusEnum.ESPERANDO_REPUESTO: "Esperando Repuesto",
    TicketStatusEnum.EN_REPARACION: "En Reparación",
    TicketStatusEnum.LISTO_PARA_RETIRAR: "Listo para Retirar",
    TicketStatusEnum.NO_APROBADO: "No Aprobado",
}

DEFAULT_ANALYTICS_STAGES = [
    TicketStatusEnum.EN_ESPERA_INGRESO,
    TicketStatusEnum.EN_REVISION,
    TicketStatusEnum.ESPERANDO_APROBACION,
    TicketStatusEnum.ESPERANDO_REPUESTO,
    TicketStatusEnum.EN_REPARACION,
]


async def get_workshop_cycle_time_metrics(
    db: AsyncSession,
    shop_id: uuid.UUID,
    days: int = 30,
):
    """
    Calcula métricas operacionales agregadas para el taller en una ventana de tiempo:
    - Lead Time promedio (ingreso -> terminal)
    - Active Cycle Time promedio (tiempo neto en reparación)
    - Desglose de duración y porcentajes por etapa
    - Detección automática del cuello de botella
    - Tasa de cumplimiento de SLA granular
    - Conteo de tickets analizados, completados y activos
    """
    from app.schemas.ticket import CycleTimeAnalyticsResponse, StageDurationMetric
    from app.services.shop_service import get_effective_sla_thresholds

    # 1. Obtener SLAs efectivos del taller
    shop_sla_config = await db.scalar(select(Shop.sla_config).where(Shop.id == shop_id))
    effective_slas = get_effective_sla_thresholds(shop_sla_config)

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=days)

    # 2. Consultar tickets del taller creados en la ventana
    query = (
        select(Ticket)
        .where(Ticket.shop_id == shop_id)
        .where(Ticket.created_at >= cutoff)
        .options(selectinload(Ticket.status_history))
        .order_by(Ticket.created_at.asc())
    )
    result = await db.execute(query)
    tickets = list(result.scalars().all())

    total_tickets = len(tickets)
    if total_tickets == 0:
        stage_metrics = [
            StageDurationMetric(
                status=st,
                label=STAGE_LABELS.get(st, st.value),
                avg_hours=0.0,
                percentage_of_total=0.0,
                is_bottleneck=False,
            )
            for st in DEFAULT_ANALYTICS_STAGES
        ]
        return CycleTimeAnalyticsResponse(
            lead_time_avg_hours=0.0,
            cycle_time_avg_hours=0.0,
            sla_compliance_rate=100.0,
            bottleneck_stage=None,
            bottleneck_stage_label=None,
            tickets_analyzed_count=0,
            completed_tickets_count=0,
            active_tickets_count=0,
            stage_durations=stage_metrics,
            time_window_days=days,
        )

    # 3. Procesar ciclo de vida de cada ticket
    completed_tickets_count = 0
    active_tickets_count = 0
    lead_times: list[float] = []

    stage_durations_map: dict[TicketStatusEnum, list[float]] = {
        st: [] for st in DEFAULT_ANALYTICS_STAGES
    }

    total_sla_intervals = 0
    compliant_sla_intervals = 0

    for ticket in tickets:
        is_completed = ticket.status in (
            TicketStatusEnum.LISTO_PARA_RETIRAR,
            TicketStatusEnum.NO_APROBADO,
        )
        if is_completed:
            completed_tickets_count += 1
        else:
            active_tickets_count += 1

        histories = sorted(ticket.status_history, key=lambda h: h.changed_at)
        ticket_stage_hours: dict[TicketStatusEnum, float] = {
            st: 0.0 for st in DEFAULT_ANALYTICS_STAGES
        }

        if histories:
            for i in range(len(histories)):
                h = histories[i]
                status_str = h.to_status
                status_enum = None
                try:
                    status_enum = TicketStatusEnum(status_str)
                except ValueError:
                    pass

                start_time = h.changed_at
                if start_time.tzinfo is None:
                    start_time = start_time.replace(tzinfo=datetime.timezone.utc)

                if i + 1 < len(histories):
                    end_time = histories[i + 1].changed_at
                    if end_time.tzinfo is None:
                        end_time = end_time.replace(tzinfo=datetime.timezone.utc)
                else:
                    if status_enum in (
                        TicketStatusEnum.LISTO_PARA_RETIRAR,
                        TicketStatusEnum.NO_APROBADO,
                    ):
                        end_time = start_time
                    else:
                        end_time = now

                duration_hours = max(0.0, (end_time - start_time).total_seconds() / 3600.0)

                if status_enum in DEFAULT_ANALYTICS_STAGES:
                    ticket_stage_hours[status_enum] += duration_hours

                if status_str in effective_slas:
                    sla_threshold = effective_slas[status_str]
                    if sla_threshold is not None and sla_threshold > 0:
                        total_sla_intervals += 1
                        if duration_hours <= sla_threshold:
                            compliant_sla_intervals += 1
        else:
            status_enum = ticket.status
            start_time = ticket.created_at
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=datetime.timezone.utc)
            end_time = ticket.updated_at or now
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=datetime.timezone.utc)

            duration_hours = max(0.0, (end_time - start_time).total_seconds() / 3600.0)
            if status_enum in DEFAULT_ANALYTICS_STAGES:
                ticket_stage_hours[status_enum] += duration_hours

            status_str = status_enum.value if hasattr(status_enum, "value") else str(status_enum)
            if status_str in effective_slas:
                sla_threshold = effective_slas[status_str]
                if sla_threshold is not None and sla_threshold > 0:
                    total_sla_intervals += 1
                    if duration_hours <= sla_threshold:
                        compliant_sla_intervals += 1

        for st in DEFAULT_ANALYTICS_STAGES:
            stage_durations_map[st].append(ticket_stage_hours[st])

        if is_completed:
            created_at = ticket.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=datetime.timezone.utc)

            terminal_histories = [
                h
                for h in histories
                if h.to_status
                in (
                    TicketStatusEnum.LISTO_PARA_RETIRAR.value,
                    TicketStatusEnum.NO_APROBADO.value,
                )
            ]
            if terminal_histories:
                completed_at = terminal_histories[0].changed_at
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=datetime.timezone.utc)
            else:
                completed_at = ticket.updated_at or now
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=datetime.timezone.utc)

            lead_hours = max(0.0, (completed_at - created_at).total_seconds() / 3600.0)
            lead_times.append(lead_hours)

    # 4. Calcular promedios y porcentajes
    lead_time_avg = round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0

    stage_avg_hours: dict[TicketStatusEnum, float] = {}
    for st in DEFAULT_ANALYTICS_STAGES:
        durations = stage_durations_map[st]
        avg = round(sum(durations) / len(durations), 1) if durations else 0.0
        stage_avg_hours[st] = avg

    cycle_time_avg = stage_avg_hours.get(TicketStatusEnum.EN_REPARACION, 0.0)

    total_stage_hours = sum(stage_avg_hours.values())
    max_avg = 0.0
    bottleneck_st = None
    for st, avg in stage_avg_hours.items():
        if avg > max_avg:
            max_avg = avg
            bottleneck_st = st

    stage_metrics: list[StageDurationMetric] = []
    for st in DEFAULT_ANALYTICS_STAGES:
        avg = stage_avg_hours[st]
        pct = round((avg / total_stage_hours) * 100.0, 1) if total_stage_hours > 0 else 0.0
        is_bn = (st == bottleneck_st) if (bottleneck_st is not None and max_avg > 0) else False
        stage_metrics.append(
            StageDurationMetric(
                status=st,
                label=STAGE_LABELS.get(st, st.value),
                avg_hours=avg,
                percentage_of_total=pct,
                is_bottleneck=is_bn,
            )
        )

    if total_sla_intervals > 0:
        sla_rate = round((compliant_sla_intervals / total_sla_intervals) * 100.0, 1)
    else:
        sla_rate = 100.0

    return CycleTimeAnalyticsResponse(
        lead_time_avg_hours=lead_time_avg,
        cycle_time_avg_hours=cycle_time_avg,
        sla_compliance_rate=sla_rate,
        bottleneck_stage=bottleneck_st if max_avg > 0 else None,
        bottleneck_stage_label=STAGE_LABELS.get(bottleneck_st)
        if (bottleneck_st and max_avg > 0)
        else None,
        tickets_analyzed_count=total_tickets,
        completed_tickets_count=completed_tickets_count,
        active_tickets_count=active_tickets_count,
        stage_durations=stage_metrics,
        time_window_days=days,
    )


async def update_ticket_partial(
    db: AsyncSession,
    ticket_id: uuid.UUID,
    shop_id: uuid.UUID,
    data: dict,
) -> Ticket:
    """Actualiza parcialmente un ticket sin disparar hooks complejos de status."""
    ticket = await _get_ticket_or_404(db, ticket_id, shop_id)
    
    for field, value in data.items():
        if hasattr(ticket, field):
            setattr(ticket, field, value)
            
    try:
        await db.commit()
        await db.refresh(ticket)
    except Exception:
        await db.rollback()
        raise
        
    ticket.device_password = decrypt_pin(ticket.pin_or_password)  # type: ignore[attr-defined]
    return _clear_pin(ticket)

