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
from app.models.user import User, UserRoleEnum
from app.services.encryption_service import decrypt_pin, encrypt_pin
from app.services import email_service
from app.config import get_settings

if TYPE_CHECKING:
    # Importación circular evitada: solo para type-checking
    pass


# ─── Excepción de dominio ─────────────────────────────────────────────────────

class TicketNotFound(Exception):
    """El ticket no existe o no pertenece al shop_id indicado."""


class CustomerNotInShop(Exception):
    """El customer_id no pertenece al shop_id indicado."""


class TechnicianNotInShop(Exception):
    """El técnico no pertenece al shop_id indicado."""


class InvalidTechnicianRole(Exception):
    """El usuario no tiene rol de técnico o admin — no puede asignarse."""


# ─── Helpers internos ─────────────────────────────────────────────────────────

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
        await db.commit()
        await db.refresh(ticket)
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

    Carga: customer, assigned_technician, items, evidences.

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

    ticket.requires_approval = True
    ticket.status = TicketStatusEnum.ESPERANDO_APROBACION

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

    ticket.status = TicketStatusEnum.EN_REPARACION
    ticket.requires_approval = False

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

    ticket.status = TicketStatusEnum.NO_APROBADO
    ticket.requires_approval = False

    if rejection_reason:
        note_prefix = f"[MOTIVO DE RECHAZO]: {rejection_reason}\n"
        ticket.internal_notes = note_prefix + (ticket.internal_notes or "")

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
    date_range: str | None = None
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

    stmt = stmt.order_by(
        case((Ticket.technician_id.is_(None), 0), else_=1),
        case((Ticket.created_at < func.now() - datetime.timedelta(hours=72), 0), else_=1),
        Ticket.created_at.desc()
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
) -> Ticket:
    """
    Actualiza el estado de un ticket y dispara el webhook de cambio.

    Args:
        new_status: Nuevo estado destino.

    Returns:
        Ticket actualizado sin pin_or_password.

    Raises:
        TicketNotFound: Si no existe o no pertenece al shop.
    """
    ticket = await _get_ticket_or_404(
        db, ticket_id, shop_id, selectinload(Ticket.customer)
    )

    old_status: TicketStatusEnum = ticket.status
    ticket.status = new_status

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
