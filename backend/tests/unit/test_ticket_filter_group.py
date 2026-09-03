"""
Tests for filter_group query parameter and synchronization with stats.
"""
import uuid
from datetime import datetime, timezone
import pytest
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.ticket import Ticket, TicketStatusEnum
from app.services import ticket_service


@pytest.mark.asyncio
async def test_list_tickets_filter_group_activos(db_session):
    # Setup test shop
    shop = Shop(
        business_name="Test Shop Filter",
        owner_name="Test Owner",
        subdomain=f"test-shop-{uuid.uuid4().hex[:8]}",
        contact_email="shop@test.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    # Setup customer
    customer = Customer(
        shop_id=shop.id,
        full_name="Juan Perez",
        phone_number="593987654321",
        email="juan@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    # Create tickets with different statuses
    ticket_statuses = [
        TicketStatusEnum.EN_ESPERA_INGRESO,
        TicketStatusEnum.EN_REVISION,
        TicketStatusEnum.EN_REPARACION,
        TicketStatusEnum.LISTO_PARA_RETIRAR,
        TicketStatusEnum.NO_APROBADO,
    ]

    for status in ticket_statuses:
        t = Ticket(
            shop_id=shop.id,
            customer_id=customer.id,
            device_brand="Apple",
            device_model="iPhone 13",
            issue_description=f"Issue for {status.value}",
            status=status,
            tracking_token=str(uuid.uuid4()),
        )
        db_session.add(t)

    await db_session.flush()

    # 1. Test get_ticket_stats
    stats = await ticket_service.get_ticket_stats(db=db_session, shop_id=shop.id)
    assert stats["total"] == 5
    assert stats["activos"] == 3
    assert stats["listos"] == 1
    assert stats["espera"] == 1

    # 2. Test list_tickets with filter_group="activos"
    tickets, total = await ticket_service.list_tickets(
        db=db_session,
        shop_id=shop.id,
        filter_group="activos",
    )
    assert total == 3
    assert len(tickets) == 3
    # Verify no LISTO_PARA_RETIRAR or NO_APROBADO in results
    returned_statuses = {t.status for t in tickets}
    assert TicketStatusEnum.LISTO_PARA_RETIRAR not in returned_statuses
    assert TicketStatusEnum.NO_APROBADO not in returned_statuses
    assert TicketStatusEnum.EN_ESPERA_INGRESO in returned_statuses
    assert TicketStatusEnum.EN_REVISION in returned_statuses
    assert TicketStatusEnum.EN_REPARACION in returned_statuses

    # 3. Test that explicit status overrides filter_group
    tickets_ready, total_ready = await ticket_service.list_tickets(
        db=db_session,
        shop_id=shop.id,
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        filter_group="activos",
    )
    assert total_ready == 1
    assert len(tickets_ready) == 1
    assert tickets_ready[0].status == TicketStatusEnum.LISTO_PARA_RETIRAR
