"""
Unit and API tests for Technician Portal and AI Copilot Backend (Phase 1).

Tests include:
- GET /technicians/me profile resolution & metrics isolation (no financial data)
- Ownership 403 verification on tickets assigned to other technicians
- POST /tickets/{id}/assign-me self-assignment and conflict handling
- POST /tickets/{id}/reveal-pin decryption and security audit trail
- Rate limiter key generation with 3-tier fallback
- Technician creation with user account linking
- TokenResponse role and full_name serialization
"""
import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from fastapi import Request

from app.main import app
from app.core.dependencies import subscription_guard
from app.core.rate_limit import get_user_rate_limit_key
from app.core.security import create_access_token, encrypt_pin
from app.models.shop import Shop
from app.models.customer import Customer
from app.models.technician import Technician
from app.models.user import User, UserRoleEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_status_history import TicketStatusHistory
from app.schemas.technician import TechnicianCreate
from app.schemas.auth import TokenResponse
from app.services import technician_service


@pytest.fixture
def mock_request():
    def _create_mock_request(user_id=None, auth_header=None, client_ip="192.168.1.50"):
        req = MagicMock(spec=Request)
        req.state = MagicMock()
        req.state.user_id = user_id
        req.headers = {}
        if auth_header:
            req.headers["Authorization"] = auth_header
        req.client = MagicMock()
        req.client.host = client_ip
        return req
    return _create_mock_request


# ─── 1. Rate Limiter Key Generation Tests ────────────────────────────────────

def test_get_user_rate_limit_key_from_request_state(mock_request):
    user_id = str(uuid.uuid4())
    req = mock_request(user_id=user_id)
    key = get_user_rate_limit_key(req)
    assert key == f"user:{user_id}"


def test_get_user_rate_limit_key_from_jwt_fallback(mock_request):
    user_id = str(uuid.uuid4())
    shop_id = str(uuid.uuid4())
    token = create_access_token(user_id=user_id, shop_id=shop_id, role="technician")

    req = mock_request(user_id=None, auth_header=f"Bearer {token}")
    key = get_user_rate_limit_key(req)
    assert key == f"user:{user_id}"


def test_get_user_rate_limit_key_from_remote_ip_fallback(mock_request):
    req = mock_request(user_id=None, auth_header=None, client_ip="203.0.113.195")
    key = get_user_rate_limit_key(req)
    assert key == "203.0.113.195"


# ─── 2. Auth Schemas & TokenResponse Tests ───────────────────────────────────

def test_token_response_schema_fields():
    resp = TokenResponse(
        access_token="fake_access",
        refresh_token="fake_refresh",
        role="technician",
        user_full_name="Pedro Técnico",
        shop_name="ElectroFix",
    )
    assert resp.role == "technician"
    assert resp.user_full_name == "Pedro Técnico"
    assert resp.shop_name == "ElectroFix"


# ─── 3. Technician Creation with User Account ────────────────────────────────

@pytest.mark.asyncio
async def test_create_technician_with_user_account(db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Tech Shop",
        owner_name="Owner",
        subdomain=f"tech-shop-{uuid.uuid4().hex[:8]}",
        contact_email="tech@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    tech_data = TechnicianCreate(
        full_name="Tech Auto Linked",
        contact="0999999999",
        declared_specialty="Smartphones",
        email="tech_linked@test.com",
        password="SecurePassword123!",
    )

    tech = await technician_service.create_technician(db_session, shop_id, tech_data)
    assert tech.id is not None
    assert tech.user_id is not None
    assert tech.full_name == "Tech Auto Linked"

    # Verify User record was created in DB
    user = await db_session.get(User, tech.user_id)
    assert user is not None
    assert user.email == "tech_linked@test.com"
    assert user.role == UserRoleEnum.technician
    assert user.shop_id == shop_id


# ─── 4. Technician Me Endpoint & Ownership Tests ──────────────────────────────

@pytest.mark.asyncio
async def test_get_technician_me_endpoint(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Portal Test Shop",
        owner_name="Owner",
        subdomain=f"portal-shop-{uuid.uuid4().hex[:8]}",
        contact_email="portal@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    tech_user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        full_name="Lucia Gomez",
        email=f"lucia-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(tech_user)
    await db_session.flush()

    technician = Technician(
        id=uuid.uuid4(),
        shop_id=shop_id,
        full_name="Lucia Gomez",
        user_id=tech_user.id,
        declared_specialty="Microsoldadura",
        is_active=True,
    )
    db_session.add(technician)

    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente Portal",
        phone_number="593988887777",
        email="cliente.portal@test.com",
    )
    db_session.add(customer)
    await db_session.flush()

    # Create 1 active ticket and 1 completed ticket for Lucia
    t1 = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Pantalla rota y touch fallando",
        diagnostic_notes="Reemplazo de pantalla OLED",
        status=TicketStatusEnum.EN_REPARACION,
        total_cost=150.00,
        tracking_token=str(uuid.uuid4()),
    )
    t2 = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=technician.id,
        device_brand="Samsung",
        device_model="Galaxy S21",
        issue_description="Batería inflada",
        diagnostic_notes="Cambio de batería",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        total_cost=60.00,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add_all([t1, t2])
    await db_session.flush()

    app.dependency_overrides[subscription_guard] = lambda: tech_user

    try:
        res = await client.get("/technicians/me")
        assert res.status_code == 200
        data = res.json()
        assert data["full_name"] == "Lucia Gomez"
        assert data["role"] == "technician"
        assert data["active_tickets_count"] == 1
        assert data["completed_tickets_count"] == 1
        assert data["declared_specialty"] == "Microsoldadura"
        # Ensure NO financial metrics are leaked
        assert "total_cost" not in data
        assert "attributed_value" not in data
        assert "delivered_value" not in data
    finally:
        app.dependency_overrides.pop(subscription_guard, None)


@pytest.mark.asyncio
async def test_verify_technician_ownership_guard_403(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="Guard Shop",
        owner_name="Owner",
        subdomain=f"guard-shop-{uuid.uuid4().hex[:8]}",
        contact_email="guard@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    # Tech 1: Marcos
    user_marcos = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        full_name="Marcos Perez",
        email=f"marcos-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    # Tech 2: Esteban
    user_esteban = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        full_name="Esteban Gomez",
        email=f"esteban-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add_all([user_marcos, user_esteban])
    await db_session.flush()

    tech_marcos = Technician(
        id=uuid.uuid4(),
        shop_id=shop_id,
        full_name="Marcos Perez",
        user_id=user_marcos.id,
        is_active=True,
    )
    tech_esteban = Technician(
        id=uuid.uuid4(),
        shop_id=shop_id,
        full_name="Esteban Gomez",
        user_id=user_esteban.id,
        is_active=True,
    )
    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente Test",
        phone_number="593900000000",
        email="cliente@test.com",
    )
    db_session.add_all([tech_marcos, tech_esteban, customer])
    await db_session.flush()

    # Ticket assigned to Marcos
    ticket_marcos = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=tech_marcos.id,
        device_brand="Xiaomi",
        device_model="Redmi Note 11",
        issue_description="Puerto de carga no funciona",
        status=TicketStatusEnum.EN_REVISION,
        tracking_token=str(uuid.uuid4()),
        pin_or_password=encrypt_pin("1234"),
    )
    # Ticket unassigned
    ticket_unassigned = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=None,
        device_brand="Motorola",
        device_model="G60",
        issue_description="No da audio",
        status=TicketStatusEnum.EN_ESPERA_INGRESO,
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add_all([ticket_marcos, ticket_unassigned])
    await db_session.flush()

    # Log in as Esteban (trying to access Marcos's ticket)
    app.dependency_overrides[subscription_guard] = lambda: user_esteban

    try:
        # 1. Esteban tries to reveal PIN of Marcos's ticket -> 403 Forbidden
        pin_res = await client.post(f"/tickets/{ticket_marcos.id}/reveal-pin")
        assert pin_res.status_code == 403
        assert "No tienes permiso" in pin_res.json()["detail"]

        # 2. Esteban tries to modify status of Marcos's ticket -> 403 Forbidden
        status_res = await client.patch(
            f"/tickets/{ticket_marcos.id}/status",
            json={"status": "EN_REPARACION"}
        )
        assert status_res.status_code == 403

        # 3. Esteban tries to auto-assign an unassigned ticket -> 200 OK
        assign_res = await client.post(f"/tickets/{ticket_unassigned.id}/assign-me")
        assert assign_res.status_code == 200
        assert assign_res.json()["technician_id"] == str(tech_esteban.id)

        # 4. Marcos tries to auto-assign the ticket now assigned to Esteban -> 409 Conflict
        app.dependency_overrides[subscription_guard] = lambda: user_marcos
        conflict_res = await client.post(f"/tickets/{ticket_unassigned.id}/assign-me")
        assert conflict_res.status_code == 409

    finally:
        app.dependency_overrides.pop(subscription_guard, None)


# ─── 5. Reveal PIN & Audit History Verification ──────────────────────────────

@pytest.mark.asyncio
async def test_reveal_pin_returns_decrypted_and_creates_audit_history(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="PIN Shop",
        owner_name="Owner",
        subdomain=f"pin-shop-{uuid.uuid4().hex[:8]}",
        contact_email="pin@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        full_name="Tech Auditor",
        email=f"auditor-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    tech = Technician(
        id=uuid.uuid4(),
        shop_id=shop_id,
        full_name="Tech Auditor",
        user_id=user.id,
        is_active=True,
    )
    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente PIN",
        phone_number="593911223344",
        email="pin.cliente@test.com",
    )
    db_session.add_all([tech, customer])
    await db_session.flush()

    raw_pin = "Patron-Z-9876"
    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=tech.id,
        device_brand="Sony",
        device_model="Xperia 1",
        issue_description="Cambio de conector",
        status=TicketStatusEnum.EN_REVISION,
        pin_or_password=encrypt_pin(raw_pin),
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    app.dependency_overrides[subscription_guard] = lambda: user

    try:
        res = await client.post(f"/tickets/{ticket.id}/reveal-pin")
        assert res.status_code == 200
        data = res.json()
        assert data["device_password"] == raw_pin

        # Check status_history table for PIN_REVEALED audit entry
        stmt = (
            TicketStatusHistory.__table__.select()
            .where(TicketStatusHistory.ticket_id == ticket.id)
            .where(TicketStatusHistory.to_status == "PIN_REVEALED")
        )
        audit_res = await db_session.execute(stmt)
        entry = audit_res.mappings().first()

        assert entry is not None
        assert entry["changed_by_user_id"] == user.id
        assert entry["reason"] == "PIN revelado por técnico"
    finally:
        app.dependency_overrides.pop(subscription_guard, None)


@pytest.mark.asyncio
async def test_reveal_pin_rate_limit_exceeded(client, db_session):
    shop_id = uuid.uuid4()
    shop = Shop(
        id=shop_id,
        business_name="RateLimit Shop",
        owner_name="Owner",
        subdomain=f"ratelimit-shop-{uuid.uuid4().hex[:8]}",
        contact_email="rl@shop.com",
        contact_whatsapp="593999999999",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(shop)
    await db_session.flush()

    user = User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.technician,
        full_name="Tech RateLimited",
        email=f"rl-{uuid.uuid4().hex[:8]}@test.com",
        password_hash="fakehash",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    tech = Technician(
        id=uuid.uuid4(),
        shop_id=shop_id,
        full_name="Tech RateLimited",
        user_id=user.id,
        is_active=True,
    )
    customer = Customer(
        shop_id=shop_id,
        full_name="Cliente RL",
        phone_number="593911223344",
        email="rl.cliente@test.com",
    )
    db_session.add_all([tech, customer])
    await db_session.flush()

    ticket = Ticket(
        shop_id=shop_id,
        customer_id=customer.id,
        technician_id=tech.id,
        device_brand="Apple",
        device_model="iPhone 12",
        issue_description="Batería",
        status=TicketStatusEnum.EN_REVISION,
        pin_or_password=encrypt_pin("1234"),
        tracking_token=str(uuid.uuid4()),
    )
    db_session.add(ticket)
    await db_session.flush()

    token = create_access_token(user_id=str(user.id), shop_id=str(shop_id), role="technician")
    headers = {"Authorization": f"Bearer {token}"}
    app.dependency_overrides[subscription_guard] = lambda: user

    try:
        # Rate limit is 15/minute: 15 succeed, 16th is 429
        responses = []
        for _ in range(16):
            res = await client.post(f"/tickets/{ticket.id}/reveal-pin", headers=headers)
            responses.append(res.status_code)

        assert responses[:15] == [200] * 15
        assert responses[15] == 429
    finally:
        app.dependency_overrides.pop(subscription_guard, None)

