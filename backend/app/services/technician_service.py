"""
Lógica de negocio para la gestión de Técnicos (Fase 2 & Fase 6).
"""
import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.technician import Technician
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_item import TicketItem
from app.schemas.technician import (
    TechnicianCreate,
    TechnicianUpdate,
    TechnicianWithMetrics,
    InferredSpecialty,
    ShopTotals,
    TechnicianMetricsTable,
)


class TechnicianDuplicate(Exception):
    pass


class TechnicianNotFound(Exception):
    pass


async def create_technician(
    db: AsyncSession, shop_id: uuid.UUID, data: TechnicianCreate
) -> Technician:
    tech = Technician(
        shop_id=shop_id,
        full_name=data.full_name,
        contact=data.contact,
        declared_specialty=data.declared_specialty,
        is_active=True,
    )
    db.add(tech)
    try:
        await db.commit()
        await db.refresh(tech)
    except IntegrityError:
        await db.rollback()
        raise TechnicianDuplicate("Ya existe un técnico con ese nombre en este taller.")
    return tech


async def get_technicians(
    db: AsyncSession, shop_id: uuid.UUID, include_inactive: bool = False
) -> list[Technician]:
    stmt = select(Technician).where(Technician.shop_id == shop_id)
    if not include_inactive:
        stmt = stmt.where(Technician.is_active == True)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_technician_by_id(
    db: AsyncSession, technician_id: uuid.UUID, shop_id: uuid.UUID
) -> Technician | None:
    result = await db.execute(
        select(Technician).where(
            Technician.id == technician_id, Technician.shop_id == shop_id
        )
    )
    return result.scalar_one_or_none()


async def update_technician(
    db: AsyncSession, technician_id: uuid.UUID, shop_id: uuid.UUID, data: TechnicianUpdate
) -> Technician:
    tech = await get_technician_by_id(db, technician_id, shop_id)
    if not tech:
        raise TechnicianNotFound("Técnico no encontrado.")

    if data.full_name is not None:
        tech.full_name = data.full_name
    if data.contact is not None:
        tech.contact = data.contact
    if data.declared_specialty is not None:
        tech.declared_specialty = data.declared_specialty

    try:
        await db.commit()
        await db.refresh(tech)
    except IntegrityError:
        await db.rollback()
        raise TechnicianDuplicate("Ya existe un técnico con ese nombre en este taller.")
    return tech


async def deactivate_technician(
    db: AsyncSession, technician_id: uuid.UUID, shop_id: uuid.UUID
) -> Technician:
    tech = await get_technician_by_id(db, technician_id, shop_id)
    if not tech:
        raise TechnicianNotFound("Técnico no encontrado.")
    tech.is_active = False
    await db.commit()
    await db.refresh(tech)
    return tech


async def reactivate_technician(
    db: AsyncSession, technician_id: uuid.UUID, shop_id: uuid.UUID
) -> Technician:
    tech = await get_technician_by_id(db, technician_id, shop_id)
    if not tech:
        raise TechnicianNotFound("Técnico no encontrado.")
    tech.is_active = True
    await db.commit()
    await db.refresh(tech)
    return tech


async def pick_least_loaded_technician(
    db: AsyncSession, shop_id: uuid.UUID
) -> Technician | None:
    """Para asignación aleatoria: menor carga de tickets activos, desempate random."""
    ACTIVE_STATUSES = [
        TicketStatusEnum.EN_ESPERA_INGRESO,
        TicketStatusEnum.EN_REVISION,
        TicketStatusEnum.ESPERANDO_APROBACION,
        TicketStatusEnum.ESPERANDO_REPUESTO,
        TicketStatusEnum.EN_REPARACION,
    ]

    load_count = (
        select(
            Ticket.technician_id,
            func.count(Ticket.id).label("active_count")
        )
        .where(Ticket.status.in_(ACTIVE_STATUSES))
        .group_by(Ticket.technician_id)
        .subquery()
    )

    stmt = (
        select(Technician)
        .outerjoin(load_count, Technician.id == load_count.c.technician_id)
        .where(Technician.shop_id == shop_id, Technician.is_active == True)
        .order_by(func.coalesce(load_count.c.active_count, 0).asc(), func.random())
        .limit(1)
    )

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _infer_specialties(diagnostic_texts: list[str]) -> list[InferredSpecialty]:
    categories = {
        "Pantalla/Display": {"emoji": "📱", "keywords": ["display", "pantalla", "lcd", "oled", "amoled", "touch", "táctil", "glass"]},
        "Batería": {"emoji": "🔋", "keywords": ["batería", "bateria", "battery", "pila"]},
        "Carga/USB": {"emoji": "⚡", "keywords": ["carga", "usb", "puerto", "flex de carga", "charging", "conector", "pin de carga"]},
        "Audio": {"emoji": "🔊", "keywords": ["audio", "parlante", "altavoz", "speaker", "auricular", "micrófono"]},
        "Cámara": {"emoji": "📷", "keywords": ["cámara", "camara", "camera", "lente"]},
        "Software": {"emoji": "💻", "keywords": ["software", "sistema", "firmware", "flash", "actualización", "reset", "factory"]},
        "Placa/Microsoldadura": {"emoji": "🔧", "keywords": ["placa", "soldadura", "microsoldadura", "motherboard", "chip", "ic", "reballing"]},
        "Carcasa/Tapa": {"emoji": "🛡️", "keywords": ["carcasa", "tapa", "housing", "frame", "marco", "back cover"]},
    }
    
    counts = {cat: 0 for cat in categories}
    for text in diagnostic_texts:
        text_lower = text.lower()
        for cat, data in categories.items():
            if any(kw in text_lower for kw in data["keywords"]):
                counts[cat] += 1
                
    sorted_cats = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    results = []
    for cat, count in sorted_cats:
        if count > 0 and len(results) < 3:
            results.append(InferredSpecialty(
                category=cat,
                emoji=categories[cat]["emoji"],
                count=count
            ))
    return results


async def get_technician_metrics(db: AsyncSession, shop_id: uuid.UUID) -> TechnicianMetricsTable:
    ACTIVE_STATUSES = [
        TicketStatusEnum.EN_ESPERA_INGRESO,
        TicketStatusEnum.EN_REVISION,
        TicketStatusEnum.ESPERANDO_APROBACION,
        TicketStatusEnum.ESPERANDO_REPUESTO,
        TicketStatusEnum.EN_REPARACION,
    ]
    
    techs = await get_technicians(db, shop_id, include_inactive=True)
    
    tickets_result = await db.execute(
        select(Ticket).where(Ticket.shop_id == shop_id, Ticket.technician_id.isnot(None))
    )
    tickets = list(tickets_result.scalars().all())
    
    ticket_ids = [t.id for t in tickets]
    ticket_items = []
    if ticket_ids:
        items_result = await db.execute(
            select(TicketItem).where(TicketItem.ticket_id.in_(ticket_ids))
        )
        ticket_items = list(items_result.scalars().all())
        
    items_by_ticket = {}
    for item in ticket_items:
        items_by_ticket.setdefault(item.ticket_id, []).append(item.description or "")

    metrics_list = []
    shop_total_tickets = 0
    shop_total_attributed = Decimal(0)
    shop_total_delivered = Decimal(0)

    for tech in techs:
        tech_tickets = [t for t in tickets if t.technician_id == tech.id]
        active_count = sum(1 for t in tech_tickets if t.status in ACTIVE_STATUSES)
        total_count = len(tech_tickets)
        
        attributed = sum((t.total_cost or Decimal(0)) for t in tech_tickets)
        delivered = sum((t.total_cost or Decimal(0)) for t in tech_tickets if t.status == TicketStatusEnum.LISTO_PARA_RETIRAR)
        
        diagnostic_texts = []
        for t in tech_tickets:
            text_parts = []
            if t.diagnostic_notes:
                text_parts.append(t.diagnostic_notes)
            text_parts.extend(items_by_ticket.get(t.id, []))
            if text_parts:
                diagnostic_texts.append(" ".join(text_parts))
                
        inferred = _infer_specialties(diagnostic_texts)
        
        shop_total_tickets += total_count
        shop_total_attributed += attributed
        shop_total_delivered += delivered
        
        metrics_list.append(
            TechnicianWithMetrics(
                id=tech.id,
                full_name=tech.full_name,
                contact=tech.contact,
                declared_specialty=tech.declared_specialty,
                is_active=tech.is_active,
                created_at=tech.created_at,
                updated_at=tech.updated_at,
                active_tickets=active_count,
                total_tickets=total_count,
                inferred_specialties=inferred,
                attributed_value=attributed,
                delivered_value=delivered,
            )
        )

    return TechnicianMetricsTable(
        technicians=metrics_list,
        shop_totals=ShopTotals(
            total_tickets=shop_total_tickets,
            total_attributed=shop_total_attributed,
            total_delivered=shop_total_delivered,
        )
    )
