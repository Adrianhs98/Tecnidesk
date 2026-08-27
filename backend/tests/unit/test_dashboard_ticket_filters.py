import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.customer import Customer
from app.models.shop import Shop
from app.models.technician import Technician
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.user import User, UserRoleEnum
from app.routers.diagnostic import dashboard_ticket_filters


@pytest.mark.asyncio
async def test_pending_yesterday_combines_status_and_date_filters(db_session):
    now = datetime.now(timezone.utc)
    shop = Shop(
        business_name="Dashboard filters",
        owner_name="Owner",
        subdomain=f"dashboard-{uuid.uuid4().hex[:8]}",
        contact_email="dashboard@example.com",
        contact_whatsapp="123456789",
    )
    db_session.add(shop)
    await db_session.flush()
    user = User(
        email=f"tech-{uuid.uuid4().hex}@example.com",
        password_hash="hash",
        full_name="Technician",
        shop_id=shop.id,
        role=UserRoleEnum.technician,
    )
    customer = Customer(shop_id=shop.id, full_name="Customer", phone_number="555", email="customer@example.com")
    db_session.add_all([user, customer])
    await db_session.flush()
    tech = Technician(user_id=user.id, shop_id=shop.id, full_name="Technician", contact="555")
    db_session.add(tech)
    await db_session.flush()

    yesterday = now - timedelta(days=1)
    matching = Ticket(shop_id=shop.id, customer_id=customer.id, technician_id=tech.id, device_brand="Samsung", device_model="A54", issue_description="Pending yesterday", status=TicketStatusEnum.EN_REPARACION, created_at=yesterday)
    ready_yesterday = Ticket(shop_id=shop.id, customer_id=customer.id, technician_id=tech.id, device_brand="Apple", device_model="12", issue_description="Ready yesterday", status=TicketStatusEnum.LISTO_PARA_RETIRAR, created_at=yesterday)
    pending_today = Ticket(shop_id=shop.id, customer_id=customer.id, technician_id=tech.id, device_brand="Xiaomi", device_model="13", issue_description="Pending today", status=TicketStatusEnum.EN_REVISION, created_at=now)
    db_session.add_all([matching, ready_yesterday, pending_today])
    await db_session.flush()

    result = await db_session.execute(select(Ticket).where(*dashboard_ticket_filters(
        shop.id, tech.id, "tickets pendientes de ayer", today=now.date()
    )))

    assert [ticket.id for ticket in result.scalars().all()] == [matching.id]
