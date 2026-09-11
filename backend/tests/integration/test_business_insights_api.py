"""
Integration tests for Business Insights Analytics REST Endpoint:
- GET /tickets/analytics/business-insights
- Threat Matrix: Route Shadowing, Admin Authorization Guard, Payload Integrity
"""
import uuid
import datetime
from datetime import timezone
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.dependencies import admin_guard
from app.database import get_db
from app.main import app
from app.models.user import User, UserRoleEnum
from app.schemas.ticket import (
    BusinessInsightsResponse,
    CustomerRecurrenceMetrics,
    GrossMarginMetrics,
)


@pytest.fixture
def mock_admin_user():
    shop_id = uuid.uuid4()
    return User(
        id=uuid.uuid4(),
        shop_id=shop_id,
        role=UserRoleEnum.admin,
        full_name="Owner Admin",
        email="admin@insights.com",
        is_active=True,
    )


def test_threat_matrix_route_shadowing_collision(mock_admin_user):
    """
    Threat: Route Shadowing / Collision
    Route /tickets/analytics/business-insights must NOT be shadowed by /{ticket_id}.
    It should return 200 OK, not a 422 UUID parsing error.
    """
    mock_response = BusinessInsightsResponse(
        time_window_days=30,
        brand_intake_ranking=[],
        brand_repair_rates=[],
        top_parts_rotation=[],
        customer_recurrence=CustomerRecurrenceMetrics(
            total_customers=0,
            recurring_customers_count=0,
            recurrence_rate=0.0,
            top_recurring_customers=[],
        ),
        technician_performance=[],
        gross_margin=GrossMarginMetrics(
            labor_revenue=0.0,
            parts_revenue=0.0,
            parts_cost=0.0,
            parts_margin=0.0,
            total_revenue=0.0,
            estimated_gross_profit=0.0,
            margin_percentage=0.0,
            labor_percentage=0.0,
            parts_percentage=0.0,
        ),
        critical_stock_alerts=[],
    )

    mock_session = AsyncMock()
    app.dependency_overrides[admin_guard] = lambda: mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        with patch(
            "app.services.ticket_service.get_workshop_business_insights",
            new=AsyncMock(return_value=mock_response),
        ):
            client = TestClient(app)
            response = client.get("/tickets/analytics/business-insights?days=30")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "brand_intake_ranking" in data
            assert "brand_repair_rates" in data
            assert "top_parts_rotation" in data
            assert "customer_recurrence" in data
            assert "technician_performance" in data
            assert "gross_margin" in data
            assert "critical_stock_alerts" in data
    finally:
        app.dependency_overrides.clear()


def test_threat_matrix_admin_guard_protection():
    """
    Threat: Privilege Escalation
    Only admin users can query business insights. Non-admin roles receive 403 Forbidden.
    """
    def mock_admin_guard_forbidden():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador para esta acción.",
        )

    mock_session = AsyncMock()
    app.dependency_overrides[admin_guard] = mock_admin_guard_forbidden
    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        client = TestClient(app)
        response = client.get("/tickets/analytics/business-insights")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "permisos de administrador" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()
