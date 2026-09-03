"""
Integration tests for /tickets endpoints (including filter_group=activos).
"""
import uuid
from datetime import datetime, timezone
import pytest
from app.main import app
from app.core.dependencies import subscription_guard
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum


@pytest.mark.asyncio
async def test_get_tickets_filter_group_activos_integration(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Shop Test API",
        owner_name="Owner",
        subdomain=f"shop-api-{uuid.uuid4().hex[:8]}",
        contact_email="owner@test.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin User",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)

    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente Test",
        phone_number="593987654321",
        email="cliente@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    # Create 4 tickets: 2 active, 2 inactive
    active_statuses = [TicketStatusEnum.EN_ESPERA_INGRESO, TicketStatusEnum.EN_REVISION]
    inactive_statuses = [TicketStatusEnum.LISTO_PARA_RETIRAR, TicketStatusEnum.NO_APROBADO]

    for status in active_statuses + inactive_statuses:
        t = Ticket(
            shop_id=shop_id,
            customer_id=customer.id,
            device_brand="Samsung",
            device_model="Galaxy S22",
            issue_description=f"Issue {status.value}",
            status=status,
            tracking_token=str(uuid.uuid4()),
        )
        db_session.add(t)

    await db_session.flush()

    # Override subscription_guard to return our user
    app.dependency_overrides[subscription_guard] = lambda: user

    try:
        # 1. Fetch stats
        stats_res = await client.get("/tickets/stats")
        assert stats_res.status_code == 200
        stats_data = stats_res.json()
        assert stats_data["total"] == 4
        assert stats_data["activos"] == 2
        assert stats_data["listos"] == 1
        assert stats_data["espera"] == 1

        # 2. Fetch list with filter_group=activos
        res = await client.get("/tickets?filter_group=activos")
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        statuses = [item["status"] for item in data["items"]]
        assert "LISTO_PARA_RETIRAR" not in statuses
        assert "NO_APROBADO" not in statuses
        assert "EN_ESPERA_INGRESO" in statuses
        assert "EN_REVISION" in statuses
    finally:
        app.dependency_overrides.pop(subscription_guard, None)


@pytest.mark.asyncio
async def test_patch_ticket_status_unassigned_en_reparacion_returns_400(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Guard Shop",
        owner_name="Owner",
        subdomain=f"guard-{uuid.uuid4().hex[:8]}",
        contact_email="guard@test.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)

    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente Guard",
        phone_number="593987654321",
        email="clienteguard@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        device_brand="Sony",
        device_model="PlayStation 5",
        issue_description="No da video",
        status=TicketStatusEnum.EN_REVISION,
        technician_id=None,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    app.dependency_overrides[subscription_guard] = lambda: user

    try:
        res = await client.patch(
            f"/tickets/{ticket.id}/status",
            json={"status": "EN_REPARACION"},
        )
        assert res.status_code == 400
        data = res.json()
        assert data["detail"] == "Debe asignar un técnico responsable antes de iniciar la reparación."
    finally:
        app.dependency_overrides.pop(subscription_guard, None)


@pytest.mark.asyncio
async def test_get_ticket_detail_includes_status_history(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="History Shop",
        owner_name="Owner",
        subdomain=f"history-{uuid.uuid4().hex[:8]}",
        contact_email="history@test.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)

    user = User(
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Admin",
        email=f"admin-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)

    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente History",
        phone_number="593987654321",
        email="clientehistory@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        device_brand="Apple",
        device_model="iPad Pro",
        issue_description="Batería degradada",
        status=TicketStatusEnum.EN_ESPERA_INGRESO,
        technician_id=None,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    app.dependency_overrides[subscription_guard] = lambda: user

    try:
        # 1. Update status to EN_REVISION
        patch_res = await client.patch(
            f"/tickets/{ticket.id}/status",
            json={"status": "EN_REVISION"},
        )
        assert patch_res.status_code == 200

        # 2. Get ticket detail
        get_res = await client.get(f"/tickets/{ticket.id}")
        assert get_res.status_code == 200
        detail_data = get_res.json()

        assert "status_history" in detail_data
        assert isinstance(detail_data["status_history"], list)
        assert len(detail_data["status_history"]) >= 1

        latest_history = detail_data["status_history"][-1]
        assert latest_history["from_status"] == "EN_ESPERA_INGRESO"
        assert latest_history["to_status"] == "EN_REVISION"
        assert latest_history["changed_by_user_id"] == str(user.id)
    finally:
        app.dependency_overrides.pop(subscription_guard, None)
