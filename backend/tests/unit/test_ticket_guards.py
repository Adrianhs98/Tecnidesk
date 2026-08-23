"""
Unit tests for technician assignment guards, status audit history, and dynamic SLA sorting.
"""
import uuid
import datetime
from datetime import timezone, timedelta
import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.shop import Shop
from app.models.customer import Customer
from app.models.technician import Technician
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_status_history import TicketStatusHistory
from app.schemas.ticket import TicketCreate
from app.services import ticket_service
from app.services.ticket_service import (
    UnassignedTechnicianError,
    SLA_THRESHOLDS_HOURS,
    is_ticket_sla_breached,
)


@pytest_asyncio.fixture
async def setup_data(db_session):
    shop = Shop(
        business_name="Guard Test Shop",
        owner_name="Owner",
        subdomain=f"guard-shop-{uuid.uuid4().hex[:8]}",
        contact_email="guard@test.com",
        contact_whatsapp="593999999999",
        created_at=datetime.datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    user = User(
        shop_id=shop.id,
        role=UserRoleEnum.admin,
        full_name="Admin Master",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)

    customer = Customer(
        shop_id=shop.id,
        full_name="Carlos Prueba",
        phone_number="593911112222",
        email="carlos@test.com",
    )
    db_session.add(customer)

    technician = Technician(
        shop_id=shop.id,
        full_name="Tech Specialist",
        is_active=True,
    )
    db_session.add(technician)
    await db_session.flush()

    return {
        "shop": shop,
        "user": user,
        "customer": customer,
        "technician": technician,
    }


# ─── 5.1: Strict Technician Assignment Guard Tests ───────────────────────────

@pytest.mark.asyncio
async def test_unassigned_technician_guard_raises_error_for_en_reparacion(db_session, setup_data):
    data = setup_data
    ticket = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        device_brand="Apple",
        device_model="MacBook Pro",
        issue_description="Falla de batería",
        status=TicketStatusEnum.EN_REVISION,
        technician_id=None,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    # Attempting to move to EN_REPARACION without technician must fail
    with pytest.raises(UnassignedTechnicianError) as exc_info:
        await ticket_service.update_ticket_status(
            db=db_session,
            ticket_id=ticket.id,
            shop_id=data["shop"].id,
            new_status=TicketStatusEnum.EN_REPARACION,
            changed_by_user_id=data["user"].id,
        )
    assert "Debe asignar un técnico responsable antes de iniciar la reparación." in str(exc_info.value)


@pytest.mark.asyncio
async def test_unassigned_technician_guard_allows_transition_when_technician_assigned(db_session, setup_data):
    data = setup_data
    ticket = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        device_brand="Apple",
        device_model="MacBook Pro",
        issue_description="Falla de batería",
        status=TicketStatusEnum.EN_REVISION,
        technician_id=data["technician"].id,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    updated = await ticket_service.update_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        shop_id=data["shop"].id,
        new_status=TicketStatusEnum.EN_REPARACION,
        changed_by_user_id=data["user"].id,
    )
    assert updated.status == TicketStatusEnum.EN_REPARACION
    assert updated.technician_id == data["technician"].id


@pytest.mark.asyncio
async def test_unassigned_technician_guard_allows_other_statuses_without_technician(db_session, setup_data):
    data = setup_data
    ticket = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        device_brand="Apple",
        device_model="iPhone 14",
        issue_description="Pantalla rota",
        status=TicketStatusEnum.EN_ESPERA_INGRESO,
        technician_id=None,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    updated = await ticket_service.update_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        shop_id=data["shop"].id,
        new_status=TicketStatusEnum.EN_REVISION,
        changed_by_user_id=data["user"].id,
    )
    assert updated.status == TicketStatusEnum.EN_REVISION


# ─── 5.2: Status History Audit Log Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_ticket_status_history_on_creation_and_transitions(db_session, setup_data):
    data = setup_data

    # 1. Create ticket via service
    create_payload = TicketCreate(
        client_email="newclient@test.com",
        client_name="New Client",
        client_phone="593900001111",
        device_brand="Dell",
        device_model="XPS 15",
        issue_description="No enciende",
        assignment_mode="unassigned",
    )
    ticket, _ = await ticket_service.create_ticket(
        db=db_session,
        shop_id=data["shop"].id,
        data=create_payload,
    )

    # Verify initial history entry
    histories_stmt = (
        select(TicketStatusHistory)
        .where(TicketStatusHistory.ticket_id == ticket.id)
        .order_by(TicketStatusHistory.changed_at.asc())
    )
    res = await db_session.execute(histories_stmt)
    entries = list(res.scalars().all())

    assert len(entries) == 1
    assert entries[0].from_status is None
    assert entries[0].to_status == TicketStatusEnum.EN_ESPERA_INGRESO.value
    assert "Creación" in (entries[0].reason or "")

    # 2. Transition to EN_REVISION
    await ticket_service.update_ticket_status(
        db=db_session,
        ticket_id=ticket.id,
        shop_id=data["shop"].id,
        new_status=TicketStatusEnum.EN_REVISION,
        changed_by_user_id=data["user"].id,
        reason="Inicio de revisión técnica",
    )

    # 3. Diagnostic update -> ESPERANDO_APROBACION
    await ticket_service.update_ticket_diagnostic(
        db=db_session,
        ticket_id=ticket.id,
        shop_id=data["shop"].id,
        diagnostic_notes="Requiere cambio de motherboard",
        labor_cost=50.0,
    )

    # 4. Token approval -> EN_REPARACION
    await ticket_service.approve_ticket_by_token(
        db=db_session,
        token=ticket.tracking_token,
    )

    # Check all history entries in order
    res = await db_session.execute(histories_stmt)
    all_entries = list(res.scalars().all())
    assert len(all_entries) == 4

    # Entry 1: None -> EN_ESPERA_INGRESO
    assert all_entries[0].to_status == "EN_ESPERA_INGRESO"

    # Entry 2: EN_ESPERA_INGRESO -> EN_REVISION
    assert all_entries[1].from_status == "EN_ESPERA_INGRESO"
    assert all_entries[1].to_status == "EN_REVISION"
    assert all_entries[1].changed_by_user_id == data["user"].id
    assert all_entries[1].reason == "Inicio de revisión técnica"

    # Entry 3: EN_REVISION -> ESPERANDO_APROBACION
    assert all_entries[2].from_status == "EN_REVISION"
    assert all_entries[2].to_status == "ESPERANDO_APROBACION"

    # Entry 4: ESPERANDO_APROBACION -> EN_REPARACION
    assert all_entries[3].from_status == "ESPERANDO_APROBACION"
    assert all_entries[3].to_status == "EN_REPARACION"


@pytest.mark.asyncio
async def test_ticket_status_history_on_rejection_by_token(db_session, setup_data):
    data = setup_data
    ticket = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        device_brand="HP",
        device_model="Pavilion",
        issue_description="Teclado dañado",
        status=TicketStatusEnum.ESPERANDO_APROBACION,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    await ticket_service.reject_ticket_by_token(
        db=db_session,
        token=ticket.tracking_token,
        rejection_reason="Muy costoso",
    )

    histories_stmt = (
        select(TicketStatusHistory)
        .where(TicketStatusHistory.ticket_id == ticket.id)
    )
    res = await db_session.execute(histories_stmt)
    entries = list(res.scalars().all())

    assert len(entries) == 1
    assert entries[0].from_status == "ESPERANDO_APROBACION"
    assert entries[0].to_status == "NO_APROBADO"
    assert entries[0].reason == "Muy costoso"


# ─── 5.3: Dynamic SLA Calculation & Combinatorial Sorting Tests ──────────────

@pytest.mark.parametrize(
    "status, elapsed_hours, expected_breached",
    [
        # EN_REVISION: threshold 24h
        (TicketStatusEnum.EN_REVISION, 23, False),
        (TicketStatusEnum.EN_REVISION, 24, True),
        (TicketStatusEnum.EN_REVISION, 30, True),
        # EN_ESPERA_INGRESO: threshold 48h
        (TicketStatusEnum.EN_ESPERA_INGRESO, 47, False),
        (TicketStatusEnum.EN_ESPERA_INGRESO, 48, True),
        # EN_REPARACION: threshold 48h
        (TicketStatusEnum.EN_REPARACION, 40, False),
        (TicketStatusEnum.EN_REPARACION, 49, True),
        # Paused / terminal statuses: always False
        (TicketStatusEnum.ESPERANDO_APROBACION, 100, False),
        (TicketStatusEnum.ESPERANDO_REPUESTO, 100, False),
        (TicketStatusEnum.LISTO_PARA_RETIRAR, 100, False),
        (TicketStatusEnum.NO_APROBADO, 100, False),
    ]
)
def test_dynamic_sla_threshold_calculation_helper(status, elapsed_hours, expected_breached):
    now = datetime.datetime.now(timezone.utc)
    created_or_updated = now - timedelta(hours=elapsed_hours)
    dummy_ticket = Ticket(
        shop_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        device_brand="Generic",
        device_model="Device",
        issue_description="Testing SLA",
        status=status,
        created_at=created_or_updated,
        updated_at=created_or_updated,
    )
    breached = is_ticket_sla_breached(dummy_ticket, now=now)
    assert breached == expected_breached


@pytest.mark.asyncio
async def test_workbench_combinatorial_sorting_priority(db_session, setup_data):
    """
    Verifies that list_tickets orders by:
    1. Unassigned tickets (technician_id IS NULL) first
    2. Dynamic SLA breached tickets (status-specific elapsed time) second
    3. Fresh assigned tickets sorted by created_at DESC third
    """
    data = setup_data
    now = datetime.datetime.now(timezone.utc)

    # 1. Fresh assigned ticket (1 hour ago)
    t_fresh_assigned = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        technician_id=data["technician"].id,
        device_brand="Apple",
        device_model="Fresh Assigned",
        issue_description="Fresh",
        status=TicketStatusEnum.EN_REVISION,
        created_at=now - timedelta(hours=1),
        updated_at=now - timedelta(hours=1),
        tracking_token=str(uuid.uuid4()),
    )

    # 2. SLA breached assigned ticket (EN_REVISION 30h ago -> breached > 24h)
    t_stale_assigned = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        technician_id=data["technician"].id,
        device_brand="Apple",
        device_model="Stale Assigned",
        issue_description="Stale SLA",
        status=TicketStatusEnum.EN_REVISION,
        created_at=now - timedelta(hours=30),
        updated_at=now - timedelta(hours=30),
        tracking_token=str(uuid.uuid4()),
    )

    # 3. Unassigned ticket (created 2 hours ago)
    t_unassigned = Ticket(
        shop_id=data["shop"].id,
        customer_id=data["customer"].id,
        technician_id=None,
        device_brand="Apple",
        device_model="Unassigned Ticket",
        issue_description="Needs tech",
        status=TicketStatusEnum.EN_ESPERA_INGRESO,
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2),
        tracking_token=str(uuid.uuid4()),
    )

    db_session.add_all([t_fresh_assigned, t_stale_assigned, t_unassigned])
    await db_session.flush()

    tickets, total = await ticket_service.list_tickets(
        db=db_session,
        shop_id=data["shop"].id,
    )

    assert total == 3
    # Check strict ordering priority
    assert tickets[0].id == t_unassigned.id, "Priority 1: Unassigned ticket must come first"
    assert tickets[1].id == t_stale_assigned.id, "Priority 2: SLA breached ticket must come second"
    assert tickets[2].id == t_fresh_assigned.id, "Priority 3: Fresh assigned ticket must come third"
