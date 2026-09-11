"""
Unit tests for workshop business insights analytics (7 KPIs):
1. Brand & Model intake ranking
2. Brand confirmed repair rate (excluding NO_APROBADO from denominator)
3. High-rotation parts with stock cross-reference
4. Customer recurrence (2+ tickets)
5. Technician throughput (resolved vs in-bench)
6. Gross margin (labor vs parts)
7. Critical stock alerts (low stock & consumption)
"""
import uuid
import datetime
from datetime import timezone, timedelta
from decimal import Decimal
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shop import Shop
from app.models.customer import Customer
from app.models.technician import Technician
from app.models.inventory import Inventory
from app.models.ticket_item import TicketItem, ItemTypeEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.schemas.ticket import BusinessInsightsResponse
from app.services.ticket_service import get_workshop_business_insights


@pytest_asyncio.fixture
async def business_insights_setup(db_session: AsyncSession):
    # Shop A
    shop_a = Shop(
        business_name="Workshop Insights A",
        owner_name="Owner A",
        subdomain=f"insights-a-{uuid.uuid4().hex[:8]}",
        contact_email="owner-a@test.com",
        contact_whatsapp="593999111111",
        created_at=datetime.datetime.now(timezone.utc),
    )
    # Shop B (for multi-tenant isolation testing)
    shop_b = Shop(
        business_name="Workshop Insights B",
        owner_name="Owner B",
        subdomain=f"insights-b-{uuid.uuid4().hex[:8]}",
        contact_email="owner-b@test.com",
        contact_whatsapp="593999222222",
        created_at=datetime.datetime.now(timezone.utc),
    )
    db_session.add_all([shop_a, shop_b])
    await db_session.flush()

    # Customers
    cust_recurring = Customer(
        shop_id=shop_a.id,
        full_name="Loyal Customer",
        phone_number="593991112233",
        email="loyal@test.com",
    )
    cust_single = Customer(
        shop_id=shop_a.id,
        full_name="One Time Customer",
        phone_number="593994445566",
        email="onetime@test.com",
    )
    cust_shop_b = Customer(
        shop_id=shop_b.id,
        full_name="Shop B Customer",
        phone_number="593997778899",
        email="shopb@test.com",
    )
    db_session.add_all([cust_recurring, cust_single, cust_shop_b])
    await db_session.flush()

    # Technicians
    tech_a1 = Technician(
        shop_id=shop_a.id,
        full_name="Technician Alpha",
        is_active=True,
    )
    tech_a2 = Technician(
        shop_id=shop_a.id,
        full_name="Technician Beta",
        is_active=True,
    )
    db_session.add_all([tech_a1, tech_a2])
    await db_session.flush()

    # Inventory
    inv_screen = Inventory(
        shop_id=shop_a.id,
        item_name="Pantalla OLED Samsung A52",
        sku="DISP-SAM-A52",
        stock_quantity=1,
        cost_price=Decimal("25.00"),
        selling_price=Decimal("50.00"),
        low_stock_alert=3,
        is_active=True,
    )
    inv_battery = Inventory(
        shop_id=shop_a.id,
        item_name="Batería iPhone 11",
        sku="BAT-IPH-11",
        stock_quantity=0,
        cost_price=Decimal("12.00"),
        selling_price=Decimal("30.00"),
        low_stock_alert=2,
        is_active=True,
    )
    inv_stock_ok = Inventory(
        shop_id=shop_a.id,
        item_name="Conector Tipo C Universal",
        sku="PIN-USB-C",
        stock_quantity=20,
        cost_price=Decimal("1.50"),
        selling_price=Decimal("10.00"),
        low_stock_alert=5,
        is_active=True,
    )
    db_session.add_all([inv_screen, inv_battery, inv_stock_ok])
    await db_session.flush()

    return {
        "shop_a": shop_a,
        "shop_b": shop_b,
        "cust_recurring": cust_recurring,
        "cust_single": cust_single,
        "cust_shop_b": cust_shop_b,
        "tech_a1": tech_a1,
        "tech_a2": tech_a2,
        "inv_screen": inv_screen,
        "inv_battery": inv_battery,
        "inv_stock_ok": inv_stock_ok,
    }


@pytest.mark.asyncio
async def test_business_insights_empty_state(db_session: AsyncSession, business_insights_setup):
    """When a workshop has no tickets, returns structured zeros and empty lists safely."""
    shop_a = business_insights_setup["shop_a"]
    insights = await get_workshop_business_insights(db=db_session, shop_id=shop_a.id, days=30)

    assert isinstance(insights, BusinessInsightsResponse)
    assert insights.time_window_days == 30
    assert insights.brand_intake_ranking == []
    assert insights.brand_repair_rates == []
    assert insights.top_parts_rotation == []
    assert insights.customer_recurrence.total_customers == 2  # cust_recurring & cust_single created
    assert insights.customer_recurrence.recurring_customers_count == 0
    assert insights.customer_recurrence.recurrence_rate == 0.0
    assert insights.gross_margin.total_revenue == 0.0
    assert insights.gross_margin.estimated_gross_profit == 0.0
    assert len(insights.critical_stock_alerts) == 2  # inv_screen and inv_battery have low stock


@pytest.mark.asyncio
async def test_business_insights_complete_metrics_and_tenant_isolation(
    db_session: AsyncSession, business_insights_setup
):
    """Accurately calculates all 7 KPIs, checks repair rate denominator rules, and isolates tenant."""
    shop_a = business_insights_setup["shop_a"]
    shop_b = business_insights_setup["shop_b"]
    cust_rec = business_insights_setup["cust_recurring"]
    cust_sin = business_insights_setup["cust_single"]
    cust_b = business_insights_setup["cust_shop_b"]
    tech1 = business_insights_setup["tech_a1"]
    tech2 = business_insights_setup["tech_a2"]
    inv_screen = business_insights_setup["inv_screen"]
    inv_battery = business_insights_setup["inv_battery"]

    now = datetime.datetime.now(timezone.utc)

    # ── Ticket 1: Samsung A52 - Ready (Repaired) by tech1 for cust_rec
    t1 = Ticket(
        shop_id=shop_a.id,
        customer_id=cust_rec.id,
        technician_id=tech1.id,
        device_brand="Samsung",
        device_model="Galaxy A52",
        issue_description="Screen broken",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        created_at=now - timedelta(days=5),
    )
    # ── Ticket 2: Samsung A52 - In Repair by tech1 for cust_rec (2nd ticket for customer)
    t2 = Ticket(
        shop_id=shop_a.id,
        customer_id=cust_rec.id,
        technician_id=tech1.id,
        device_brand="Samsung",
        device_model="Galaxy A52",
        issue_description="Battery drained",
        status=TicketStatusEnum.EN_REPARACION,
        created_at=now - timedelta(days=2),
    )
    # ── Ticket 3: Apple iPhone 11 - Rejected / Not Approved by cust_sin
    t3 = Ticket(
        shop_id=shop_a.id,
        customer_id=cust_sin.id,
        technician_id=tech2.id,
        device_brand="Apple",
        device_model="iPhone 11",
        issue_description="Water damage",
        status=TicketStatusEnum.NO_APROBADO,
        created_at=now - timedelta(days=3),
    )
    # ── Ticket 4: Apple iPhone 11 - Waiting Part (Confirmed Repair)
    t4 = Ticket(
        shop_id=shop_a.id,
        customer_id=cust_rec.id,
        technician_id=tech2.id,
        device_brand="Apple",
        device_model="iPhone 11",
        issue_description="Charging port broken",
        status=TicketStatusEnum.ESPERANDO_REPUESTO,
        created_at=now - timedelta(days=1),
    )
    # ── Ticket B: Belongs to Shop B (must not contaminate Shop A metrics)
    tb = Ticket(
        shop_id=shop_b.id,
        customer_id=cust_b.id,
        device_brand="Xiaomi",
        device_model="Redmi Note 10",
        issue_description="Shop B issue",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        created_at=now - timedelta(days=1),
    )
    db_session.add_all([t1, t2, t3, t4, tb])
    await db_session.flush()

    # Add Ticket Items for Shop A
    # t1: 1 screen ($50 rev, $25 cost) + 1 labor ($20 rev)
    item_t1_part = TicketItem(
        ticket_id=t1.id,
        inventory_id=inv_screen.id,
        item_type=ItemTypeEnum.part,
        description="Pantalla OLED Samsung A52",
        quantity=1,
        unit_price=Decimal("50.00"),
    )
    item_t1_labor = TicketItem(
        ticket_id=t1.id,
        item_type=ItemTypeEnum.labor,
        description="Instalación de módulo display",
        quantity=1,
        unit_price=Decimal("20.00"),
    )
    # t2: 2 batteries ($30 each, $12 cost each)
    item_t2_part = TicketItem(
        ticket_id=t2.id,
        inventory_id=inv_battery.id,
        item_type=ItemTypeEnum.part,
        description="Batería iPhone 11",
        quantity=2,
        unit_price=Decimal("30.00"),
    )
    # t3 (NO_APROBADO): should be ignored in parts & revenue
    item_t3_part = TicketItem(
        ticket_id=t3.id,
        item_type=ItemTypeEnum.part,
        description="Presupuesto no aprobado",
        quantity=1,
        unit_price=Decimal("100.00"),
    )
    db_session.add_all([item_t1_part, item_t1_labor, item_t2_part, item_t3_part])
    await db_session.flush()

    # Execute service for Shop A
    insights = await get_workshop_business_insights(db=db_session, shop_id=shop_a.id, days=30)

    # 1. Brand Ranking: Samsung (2), Apple (2). Total = 4 tickets for Shop A. Xiaomi from Shop B excluded!
    assert len(insights.brand_intake_ranking) == 2
    brands = {b.brand: b for b in insights.brand_intake_ranking}
    assert "Samsung" in brands
    assert "Apple" in brands
    assert "Xiaomi" not in brands
    assert brands["Samsung"].total_tickets == 2
    assert brands["Samsung"].percentage == 50.0
    assert brands["Samsung"].top_models[0].model == "Galaxy A52"
    assert brands["Samsung"].top_models[0].count == 2

    # 2. Brand Repair Rates & Denominator Rule:
    # Apple has 2 tickets: 1 ESPERANDO_REPUESTO (confirmed) and 1 NO_APROBADO (rejected).
    # Denominator = total (2) - rejected (1) = 1 valid intake!
    # Confirmed repairs = 1.
    # repair_rate = (1 / 1) * 100.0 = 100.0%
    apple_rate = next(r for r in insights.brand_repair_rates if r.brand == "Apple")
    assert apple_rate.total_tickets == 2
    assert apple_rate.confirmed_repairs == 1
    assert apple_rate.rejected_repairs == 1
    assert apple_rate.repair_rate == 100.0

    # Samsung has 2 tickets: 1 LISTO_PARA_RETIRAR, 1 EN_REPARACION. 0 NO_APROBADO.
    # repair_rate = (2 / 2) * 100.0 = 100.0%
    samsung_rate = next(r for r in insights.brand_repair_rates if r.brand == "Samsung")
    assert samsung_rate.total_tickets == 2
    assert samsung_rate.confirmed_repairs == 2
    assert samsung_rate.rejected_repairs == 0
    assert samsung_rate.repair_rate == 100.0

    # 3. High Rotation Parts:
    # Batería iPhone 11 had quantity 2. Pantalla OLED Samsung A52 had quantity 1.
    assert len(insights.top_parts_rotation) == 2
    top_part = insights.top_parts_rotation[0]
    assert top_part.item_name == "Batería iPhone 11"
    assert top_part.units_used == 2
    assert top_part.total_revenue == 60.0
    assert top_part.current_stock == 0
    assert top_part.is_low_stock is True

    # 4. Customer Recurrence:
    # cust_rec has 3 tickets (t1, t2, t4) >= 2 tickets!
    # cust_sin has 1 ticket.
    # Total customers = 2. Recurring = 1. Recurrence rate = 50.0%
    assert insights.customer_recurrence.total_customers == 2
    assert insights.customer_recurrence.recurring_customers_count == 1
    assert insights.customer_recurrence.recurrence_rate == 50.0
    assert len(insights.customer_recurrence.top_recurring_customers) == 1
    assert insights.customer_recurrence.top_recurring_customers[0].full_name == "Loyal Customer"
    assert insights.customer_recurrence.top_recurring_customers[0].ticket_count == 3

    # 5. Technician Performance:
    # tech1: 1 resolved (t1), 1 active in bench (t2), total = 2. completion_rate = 50.0%
    # tech2: 0 resolved, 1 active in bench (t4), 1 rejected (t3), total = 2.
    tech_metrics = {t.technician_name: t for t in insights.technician_performance}
    assert tech_metrics["Technician Alpha"].resolved_count == 1
    assert tech_metrics["Technician Alpha"].active_in_bench_count == 1
    assert tech_metrics["Technician Alpha"].total_assigned == 2
    assert tech_metrics["Technician Alpha"].completion_rate == 50.0

    assert tech_metrics["Technician Beta"].resolved_count == 0
    assert tech_metrics["Technician Beta"].active_in_bench_count == 1

    # 6. Gross Margin:
    # t1: labor rev = $20.00. parts rev = $50.00, parts cost = $25.00
    # t2: parts rev = 2 * $30 = $60.00, parts cost = 2 * $12 = $24.00
    # Total labor rev = $20.00. Total parts rev = $110.00. Total parts cost = $49.00
    # Total revenue = $130.00.
    # Parts margin = $110.00 - $49.00 = $61.00.
    # Gross profit = labor rev ($20.00) + parts margin ($61.00) = $81.00.
    # Margin % = (81.00 / 130.00) * 100 = 62.3%
    gm = insights.gross_margin
    assert gm.labor_revenue == 20.0
    assert gm.parts_revenue == 110.0
    assert gm.parts_cost == 49.0
    assert gm.parts_margin == 61.0
    assert gm.total_revenue == 130.0
    assert gm.estimated_gross_profit == 81.0
    assert gm.margin_percentage == 62.3

    # 7. Critical Stock Alerts:
    # inv_battery: stock 0, used 2 in period -> CRITICO
    # inv_screen: stock 1, used 1 in period -> BAJO
    # inv_stock_ok: stock 20 > 5 -> not in alerts
    alert_names = [a.item_name for a in insights.critical_stock_alerts]
    assert "Batería iPhone 11" in alert_names
    assert "Pantalla OLED Samsung A52" in alert_names
    assert "Conector Tipo C Universal" not in alert_names

    battery_alert = next(a for a in insights.critical_stock_alerts if a.item_name == "Batería iPhone 11")
    assert battery_alert.current_stock == 0
    assert battery_alert.units_used_in_period == 2
    assert battery_alert.alert_level == "CRITICO"
