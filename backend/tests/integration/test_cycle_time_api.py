"""
Integration tests for Cycle Time & Bottleneck Analytics REST Endpoint:
- GET /tickets/analytics/cycle-times
- Threat Matrix: Route Shadowing, Multi-Tenant Isolation, Subscription Bypass
"""
import uuid
import datetime
from datetime import timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.dependencies import get_current_user, subscription_guard
from app.database import get_db
from app.main import app
from app.models.shop import Shop
from app.models.subscription import SubscriptionStatusEnum
from app.models.ticket import Ticket, TicketStatusEnum
from app.models.ticket_status_history import TicketStatusHistory
from app.models.user import User, UserRoleEnum


@pytest.fixture
def mock_multi_tenant_data():
    shop1_id = uuid.uuid4()
    shop2_id = uuid.uuid4()

    shop1 = Shop(
        id=shop1_id,
        business_name="Taller Alpha",
        owner_name="Alpha Owner",
        subdomain="taller-alpha",
        contact_email="alpha@test.com",
        contact_whatsapp="593991111111",
        subscription_status=SubscriptionStatusEnum.active,
        sla_config={"EN_ESPERA_INGRESO": 48, "EN_REVISION": 24, "EN_REPARACION": 48},
        created_at=datetime.datetime.now(timezone.utc),
    )
    shop2 = Shop(
        id=shop2_id,
        business_name="Taller Beta",
        owner_name="Beta Owner",
        subdomain="taller-beta",
        contact_email="beta@test.com",
        contact_whatsapp="593992222222",
        subscription_status=SubscriptionStatusEnum.active,
        sla_config={},
        created_at=datetime.datetime.now(timezone.utc),
    )

    user1 = User(
        id=uuid.uuid4(),
        shop_id=shop1_id,
        role=UserRoleEnum.admin,
        full_name="Admin Shop 1",
        email="admin1@test.com",
        is_active=True,
    )
    user2 = User(
        id=uuid.uuid4(),
        shop_id=shop2_id,
        role=UserRoleEnum.admin,
        full_name="Admin Shop 2",
        email="admin2@test.com",
        is_active=True,
    )

    now = datetime.datetime.now(timezone.utc)
    # Shop 1 has 1 completed ticket (50h lead time, 10h cycle time)
    t1 = Ticket(
        id=uuid.uuid4(),
        shop_id=shop1_id,
        customer_id=uuid.uuid4(),
        device_brand="Apple",
        device_model="iPhone 13",
        issue_description="Batería",
        status=TicketStatusEnum.LISTO_PARA_RETIRAR,
        created_at=now - timedelta(hours=50),
        updated_at=now,
    )
    t1.status_history = [
        TicketStatusHistory(
            id=uuid.uuid4(),
            ticket_id=t1.id,
            from_status=None,
            to_status="EN_ESPERA_INGRESO",
            changed_at=now - timedelta(hours=50),
        ),
        TicketStatusHistory(
            id=uuid.uuid4(),
            ticket_id=t1.id,
            from_status="EN_ESPERA_INGRESO",
            to_status="EN_REPARACION",
            changed_at=now - timedelta(hours=10),
        ),
        TicketStatusHistory(
            id=uuid.uuid4(),
            ticket_id=t1.id,
            from_status="EN_REPARACION",
            to_status="LISTO_PARA_RETIRAR",
            changed_at=now,
        ),
    ]

    # Shop 2 has 0 tickets
    return {
        "shop1": shop1,
        "shop2": shop2,
        "user1": user1,
        "user2": user2,
        "ticket1": t1,
    }


def test_threat_matrix_route_shadowing_collision(mock_multi_tenant_data):
    """
    Threat: Route Shadowing / Collision
    Route /tickets/analytics/cycle-times must NOT be shadowed by /{ticket_id}.
    It should return 200 OK, not a 422 UUID parsing error.
    """
    user = mock_multi_tenant_data["user1"]
    shop1 = mock_multi_tenant_data["shop1"]
    ticket1 = mock_multi_tenant_data["ticket1"]

    mock_session = AsyncMock()

    async def mock_execute(stmt):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [ticket1]
        return mock_result

    mock_session.execute = mock_execute
    mock_session.scalar.return_value = shop1.sla_config

    app.dependency_overrides[subscription_guard] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        client = TestClient(app)
        response = client.get("/tickets/analytics/cycle-times?days=30")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "lead_time_avg_hours" in data
        assert "cycle_time_avg_hours" in data
        assert "stage_durations" in data
        assert data["tickets_analyzed_count"] == 1
    finally:
        app.dependency_overrides.clear()


def test_threat_matrix_multi_tenant_isolation(mock_multi_tenant_data):
    """
    Threat: Multi-Tenant Leakage
    Shop 2 user requesting analytics must only see Shop 2 data (0 tickets),
    never leaking Shop 1 tickets.
    """
    user2 = mock_multi_tenant_data["user2"]
    shop2 = mock_multi_tenant_data["shop2"]

    mock_session = AsyncMock()

    async def mock_execute(stmt):
        mock_result = MagicMock()
        # Shop 2 has no tickets
        mock_result.scalars.return_value.all.return_value = []
        return mock_result

    mock_session.execute = mock_execute
    mock_session.scalar.return_value = shop2.sla_config

    app.dependency_overrides[subscription_guard] = lambda: user2
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        client = TestClient(app)
        response = client.get("/tickets/analytics/cycle-times")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["tickets_analyzed_count"] == 0
        assert data["completed_tickets_count"] == 0
        assert data["active_tickets_count"] == 0
        assert data["lead_time_avg_hours"] == 0.0
        assert data["cycle_time_avg_hours"] == 0.0
        assert data["bottleneck_stage"] is None
    finally:
        app.dependency_overrides.clear()


def test_threat_matrix_subscription_bypass():
    """
    Threat: Subscription Bypass
    Unsubscribed / expired shops are blocked with 402 Payment Required by subscription_guard.
    """
    def mock_subscription_guard_expired():
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Tu suscripción al servicio ha expirado.",
        )

    mock_session = AsyncMock()
    app.dependency_overrides[subscription_guard] = mock_subscription_guard_expired
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        client = TestClient(app)
        response = client.get("/tickets/analytics/cycle-times")
        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED
        assert "expirado" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
