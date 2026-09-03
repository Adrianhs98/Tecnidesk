"""
Integration tests for Shop SLA Configuration REST Endpoints:
- GET /shops/sla-config
- PATCH /shops/sla-config
- RBAC guards (admin_guard, subscription_guard)
- Multi-tenant isolation between workshops
- Validation error responses (422)
"""
import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.core.dependencies import admin_guard, get_current_user, subscription_guard
from app.database import get_db
from app.main import app
from app.models.shop import Shop
from app.models.user import User, UserRoleEnum
from app.services.shop_service import (
    DEFAULT_SLA_THRESHOLDS_HOURS,
    get_shop_sla_config,
    update_shop_sla_config,
)


@pytest.fixture
def mock_shops():
    shop1_id = uuid.uuid4()
    shop2_id = uuid.uuid4()

    shop1 = Shop(
        id=shop1_id,
        business_name="Taller Alfa",
        owner_name="Alfa Owner",
        subdomain="taller-alfa",
        contact_email="alfa@taller.com",
        contact_whatsapp="593991111111",
        sla_config={},
    )
    shop2 = Shop(
        id=shop2_id,
        business_name="Taller Beta",
        owner_name="Beta Owner",
        subdomain="taller-beta",
        contact_email="beta@taller.com",
        contact_whatsapp="593992222222",
        sla_config={"EN_REVISION": 6},
    )
    return {shop1_id: shop1, shop2_id: shop2}


@pytest.fixture
def mock_admin_user(mock_shops):
    shop1_id = list(mock_shops.keys())[0]
    return User(
        id=uuid.uuid4(),
        shop_id=shop1_id,
        role=UserRoleEnum.admin,
        full_name="Admin Taller Alfa",
        email="admin@alfa.com",
        is_active=True,
    )


@pytest.fixture
def mock_tech_user(mock_shops):
    shop1_id = list(mock_shops.keys())[0]
    return User(
        id=uuid.uuid4(),
        shop_id=shop1_id,
        role=UserRoleEnum.technician,
        full_name="Tech Taller Alfa",
        email="tech@alfa.com",
        is_active=True,
    )


@pytest.fixture
def mock_db_session(mock_shops):
    session = AsyncMock()

    async def mock_execute(stmt):
        mock_result = MagicMock()
        # Find which shop_id is queried
        queried_shop = None
        for shop_id, shop in mock_shops.items():
            if str(shop_id) in str(stmt) or shop.id in getattr(stmt, "_where_criteria", ()):
                queried_shop = shop
                break
        if queried_shop is None:
            # default to first shop
            queried_shop = list(mock_shops.values())[0]

        mock_result.scalar_one_or_none.return_value = queried_shop
        mock_result.scalar_one.return_value = queried_shop
        mock_result.scalars.return_value.all.return_value = [queried_shop]
        return mock_result

    session.execute = mock_execute
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


def test_get_sla_config_success(mock_admin_user, mock_db_session):
    """GET /shops/sla-config returns 200 with effective, custom, and default SLA hours."""
    app.dependency_overrides[subscription_guard] = lambda: mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db_session

    try:
        client = TestClient(app)
        response = client.get("/shops/sla-config")
        assert response.status_code == 200
        data = response.json()
        assert "effective_thresholds" in data
        assert "custom_thresholds" in data
        assert "default_thresholds" in data
        assert data["default_thresholds"]["EN_REVISION"] == 24
        assert data["effective_thresholds"]["EN_ESPERA_INGRESO"] == 48
    finally:
        app.dependency_overrides.clear()


def test_patch_sla_config_success(mock_admin_user, mock_db_session, mock_shops):
    """PATCH /shops/sla-config updates tenant SLA config and returns 200 with merged thresholds."""
    app.dependency_overrides[admin_guard] = lambda: mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db_session

    try:
        client = TestClient(app)
        payload = {
            "custom_thresholds": {
                "EN_REVISION": 12,
                "EN_REPARACION": 36,
            }
        }
        response = client.patch("/shops/sla-config", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["custom_thresholds"]["EN_REVISION"] == 12
        assert data["custom_thresholds"]["EN_REPARACION"] == 36
        assert data["effective_thresholds"]["EN_REVISION"] == 12
        assert data["effective_thresholds"]["EN_REPARACION"] == 36
        assert data["effective_thresholds"]["EN_ESPERA_INGRESO"] == 48  # untouched default
    finally:
        app.dependency_overrides.clear()


def test_patch_sla_config_validation_errors(mock_admin_user, mock_db_session):
    """PATCH /shops/sla-config returns 422 on invalid hours (<1, >720) or invalid status keys."""
    app.dependency_overrides[admin_guard] = lambda: mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db_session

    try:
        client = TestClient(app)

        # 1. Invalid status name
        res1 = client.patch("/shops/sla-config", json={"custom_thresholds": {"INVALID_STATUS": 24}})
        assert res1.status_code == 422

        # 2. Hours less than 1
        res2 = client.patch("/shops/sla-config", json={"custom_thresholds": {"EN_REVISION": 0}})
        assert res2.status_code == 422

        # 3. Hours greater than 720
        res3 = client.patch("/shops/sla-config", json={"custom_thresholds": {"EN_REVISION": 721}})
        assert res3.status_code == 422

        # 4. Non-integer hours
        res4 = client.patch("/shops/sla-config", json={"custom_thresholds": {"EN_REVISION": "twenty"}})
        assert res4.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_sla_config_rbac_non_admin_forbidden(mock_tech_user, mock_db_session):
    """Technicians can read GET /shops/sla-config (200), but cannot modify PATCH /shops/sla-config (403)."""
    async def tech_admin_guard():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol de administrador para esta acción.",
        )

    app.dependency_overrides[subscription_guard] = lambda: mock_tech_user
    app.dependency_overrides[admin_guard] = tech_admin_guard
    app.dependency_overrides[get_db] = lambda: mock_db_session

    try:
        client = TestClient(app)
        get_res = client.get("/shops/sla-config")
        assert get_res.status_code == 200
        data = get_res.json()
        assert "effective_thresholds" in data

        patch_res = client.patch("/shops/sla-config", json={"custom_thresholds": {"EN_REVISION": 10}})
        assert patch_res.status_code == 403
        assert "administrador" in patch_res.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_sla_config_unauthenticated_unauthorized(mock_db_session):
    """Unauthenticated requests without bearer token return 401 Unauthorized."""
    async def unauth_guard():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no proporcionado o inválido.",
        )

    app.dependency_overrides[subscription_guard] = unauth_guard
    app.dependency_overrides[get_db] = lambda: mock_db_session

    try:
        client = TestClient(app)
        res = client.get("/shops/sla-config")
        assert res.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_sla_config_multitenant_isolation(mock_shops):
    """Modifying Shop 1's SLA config does NOT alter Shop 2's SLA config."""
    shop1_id = list(mock_shops.keys())[0]
    shop2_id = list(mock_shops.keys())[1]

    db_mock = AsyncMock()

    def get_shop_mock(stmt):
        res = MagicMock()
        params = stmt.compile().params if hasattr(stmt, "compile") else {}
        if shop1_id in params.values() or str(shop1_id) in str(params):
            res.scalar_one_or_none.return_value = mock_shops[shop1_id]
        elif shop2_id in params.values() or str(shop2_id) in str(params):
            res.scalar_one_or_none.return_value = mock_shops[shop2_id]
        else:
            res.scalar_one_or_none.return_value = None
        return res

    db_mock.execute = AsyncMock(side_effect=get_shop_mock)
    db_mock.flush = AsyncMock()
    db_mock.add = MagicMock()

    # Update Shop 1
    await update_shop_sla_config(db_mock, shop1_id, {"EN_REVISION": 8})

    # Assert Shop 1 updated
    assert mock_shops[shop1_id].sla_config == {"EN_REVISION": 8}

    # Assert Shop 2 remains unchanged
    assert mock_shops[shop2_id].sla_config == {"EN_REVISION": 6}
