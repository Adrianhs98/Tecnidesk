"""
Unit tests for workshop cycle time, lead time, bottleneck detection, and SLA compliance analytics engine.
"""
import uuid
import datetime
from datetime import timezone, timedelta
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shop import Shop
from app.models.customer import Customer
from app.models.technician import Technician
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_status_history import TicketStatusHistory
from app.schemas.ticket import CycleTimeAnalyticsResponse, StageDurationMetric
from app.services.ticket_service import get_workshop_cycle_time_metrics


@pytest_asyncio.fixture
async def analytics_setup(db_session: AsyncSession):
    shop = Shop(
        business_name="Analytics Test Shop",
        owner_name="Owner",
        subdomain=f"analytics-{uuid.uuid4().hex[:8]}",
        contact_email="analytics@test.com",
        contact_whatsapp="593999999999",
        sla_config={"EN_ESPERA_INGRESO": 48, "EN_REVISION": 24, "EN_REPARACION": 48},
        created_at=datetime.datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    user = User(
        shop_id=shop.id,
        role=UserRoleEnum.admin,
        full_name="Admin User",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)

    customer = Customer(
        shop_id=shop.id,
        full_name="Customer Test",
        phone_number="593911112222",
        email="customer@test.com",
    )
    db_session.add(customer)

    technician = Technician(
        shop_id=shop.id,
        full_name="Tech Master",
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


@pytest.mark.asyncio
async def test_analytics_zero_tickets_fallback(db_session: AsyncSession, analytics_setup):
    """When a shop has zero tickets in the time window, returns safe 0.0 values without error."""
    shop = analytics_setup["shop"]
    metrics = await get_workshop_cycle_time_metrics(db=db_session, shop_id=shop.id, days=30)

    assert isinstance(metrics, CycleTimeAnalyticsResponse)
    assert metrics.tickets_analyzed_count == 0
    assert metrics.completed_tickets_count == 0
    assert metrics.active_tickets_count == 0
    assert metrics.lead_time_avg_hours == 0.0
    assert metrics.cycle_time_avg_hours == 0.0
    assert metrics.sla_compliance_rate == 100.0
    assert metrics.bottleneck_stage is None
    assert metrics.bottleneck_stage_label is None
    assert metrics.time_window_days == 30
    assert len(metrics.stage_durations) > 0
    for stage in metrics.stage_durations:
        assert isinstance(stage, StageDurationMetric)
        assert stage.avg_hours == 0.0
        assert stage.percentage_of_total == 0.0
        assert stage.is_bottleneck is False


@pytest.mark.asyncio
async def test_analytics_single_completed_ticket(db_session: AsyncSession, analytics_setup):
    """Accurately calculates lead time, active cycle time, stage breakdown, and bottleneck."""
    shop = analytics_setup["shop"]
    customer = analytics_setup["customer"]
    technician = analytics_setup["technician"]

    now = datetime.datetime.now(timezone.utc)
    t0 = now - timedelta(hours=50)  # created
    t1 = t0 + timedelta(hours=10)  # to EN_REVISION (10h in EN_ESPERA_INGRESO)
    t2 = t1 + timedelta(hours=30)  # to EN_REPARACION (30h in EN_REVISION - SLA breach!)
    t3 = t2 + timedelta(hours=10)  # to LISTO_PARA_RETIRAR (10h in EN_REPARACION)

    ticket = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Samsung",
        device_model="Galaxy S22",
        issue_description="Batería agotada",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        created_at=t0,
        updated_at=t3,
    )
    db_session.add(ticket)
    await db_session.flush()

    h0 = TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=None,
        to_status=TicketStatusEnum.EN_ESPERA_INGRESO.value,
        changed_at=t0,
    )
    h1 = TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=TicketStatusEnum.EN_ESPERA_INGRESO.value,
        to_status=TicketStatusEnum.EN_REVISION.value,
        changed_at=t1,
    )
    h2 = TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=TicketStatusEnum.EN_REVISION.value,
        to_status=TicketStatusEnum.EN_REPARACION.value,
        changed_at=t2,
    )
    h3 = TicketStatusHistory(
        ticket_id=ticket.id,
        from_status=TicketStatusEnum.EN_REPARACION.value,
        to_status=TicketStatusEnum.LISTO_PARA_RETIRAR.value,
        changed_at=t3,
    )
    db_session.add_all([h0, h1, h2, h3])
    await db_session.flush()

    metrics = await get_workshop_cycle_time_metrics(db=db_session, shop_id=shop.id, days=30)

    assert metrics.tickets_analyzed_count == 1
    assert metrics.completed_tickets_count == 1
    assert metrics.active_tickets_count == 0
    # Total lead time = 50 hours
    assert metrics.lead_time_avg_hours == pytest.approx(50.0, 0.1)
    # Active cycle time (in EN_REPARACION) = 10 hours
    assert metrics.cycle_time_avg_hours == pytest.approx(10.0, 0.1)
    # Bottleneck stage is EN_REVISION (30 hours)
    assert metrics.bottleneck_stage == TicketStatusEnum.EN_REVISION
    assert metrics.bottleneck_stage_label == "En Revisión"

    # Check stage breakdown
    durations_dict = {s.status: s for s in metrics.stage_durations}
    assert durations_dict[TicketStatusEnum.EN_ESPERA_INGRESO].avg_hours == pytest.approx(10.0, 0.1)
    assert durations_dict[TicketStatusEnum.EN_REVISION].avg_hours == pytest.approx(30.0, 0.1)
    assert durations_dict[TicketStatusEnum.EN_REVISION].is_bottleneck is True
    assert durations_dict[TicketStatusEnum.EN_REPARACION].avg_hours == pytest.approx(10.0, 0.1)
    assert durations_dict[TicketStatusEnum.EN_REPARACION].is_bottleneck is False

    # SLA compliance:
    # EN_ESPERA_INGRESO: 10h <= 48h -> OK
    # EN_REVISION: 30h > 24h -> Breach
    # EN_REPARACION: 10h <= 48h -> OK
    # 2 out of 3 compliant -> 66.7%
    assert metrics.sla_compliance_rate == pytest.approx(66.7, 0.5)


@pytest.mark.asyncio
async def test_analytics_active_tickets_and_time_window(db_session: AsyncSession, analytics_setup):
    """Calculates metrics for active tickets up to current time and filters out older tickets."""
    shop = analytics_setup["shop"]
    customer = analytics_setup["customer"]
    technician = analytics_setup["technician"]

    now = datetime.datetime.now(timezone.utc)

    # Ticket 1: Active ticket created 5 hours ago in EN_REVISION
    t1_created = now - timedelta(hours=5)
    t1 = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Apple",
        device_model="iPhone 14",
        issue_description="Pantalla rota",
        status=TicketStatusEnum.EN_REVISION,
        created_at=t1_created,
    )
    db_session.add(t1)
    await db_session.flush()

    h_t1_0 = TicketStatusHistory(
        ticket_id=t1.id,
        from_status=None,
        to_status=TicketStatusEnum.EN_ESPERA_INGRESO.value,
        changed_at=t1_created,
    )
    h_t1_1 = TicketStatusHistory(
        ticket_id=t1.id,
        from_status=TicketStatusEnum.EN_ESPERA_INGRESO.value,
        to_status=TicketStatusEnum.EN_REVISION.value,
        changed_at=t1_created + timedelta(hours=2),
    )
    db_session.add_all([h_t1_0, h_t1_1])

    # Ticket 2: Old ticket outside 7-day window (created 15 days ago)
    t2_created = now - timedelta(days=15)
    t2 = Ticket(
        shop_id=shop.id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        issue_description="Puerto de carga",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        created_at=t2_created,
        updated_at=t2_created + timedelta(hours=20),
    )
    db_session.add(t2)
    await db_session.flush()

    h_t2_0 = TicketStatusHistory(
        ticket_id=t2.id,
        from_status=None,
        to_status=TicketStatusEnum.EN_ESPERA_INGRESO.value,
        changed_at=t2_created,
    )
    db_session.add(h_t2_0)
    await db_session.flush()

    # Query with 7-day window -> Only Ticket 1 is included
    metrics_7d = await get_workshop_cycle_time_metrics(db=db_session, shop_id=shop.id, days=7)
    assert metrics_7d.tickets_analyzed_count == 1
    assert metrics_7d.active_tickets_count == 1
    assert metrics_7d.completed_tickets_count == 0
    assert metrics_7d.time_window_days == 7

    # Query with 30-day window -> Both Ticket 1 and Ticket 2 are included
    metrics_30d = await get_workshop_cycle_time_metrics(db=db_session, shop_id=shop.id, days=30)
    assert metrics_30d.tickets_analyzed_count == 2
    assert metrics_30d.active_tickets_count == 1
    assert metrics_30d.completed_tickets_count == 1
