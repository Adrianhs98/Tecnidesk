import uuid
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import get_settings
from app.core.dependencies import superadmin_key_guard, get_db
from app.main import app


@pytest.mark.asyncio
async def test_superadmin_key_guard_missing_header():
    """Requirement: Reject requests without the platform key (401)"""
    with pytest.raises(HTTPException) as exc_info:
        await superadmin_key_guard(api_key=None)
    
    assert exc_info.value.status_code == 401
    assert "Se requiere la cabecera X-Superadmin-Key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_superadmin_key_guard_invalid_key():
    """Requirement: Reject requests with an incorrect platform key (403)"""
    with pytest.raises(HTTPException) as exc_info:
        await superadmin_key_guard(api_key="invalid-secret-key")
    
    assert exc_info.value.status_code == 403
    assert "Clave de superadministrador inválida" in exc_info.value.detail


@pytest.mark.asyncio
async def test_superadmin_key_guard_valid_key():
    """Requirement: Accept requests with valid platform key"""
    settings = get_settings()
    valid_key = settings.superadmin_api_key
    
    result = await superadmin_key_guard(api_key=valid_key)
    assert result == valid_key


def test_activate_shop_endpoint_missing_key_returns_401():
    """Scenario: Missing header returns 401 via HTTP call (TestClient)"""
    client = TestClient(app)
    payload = {
        "shop_id": str(uuid.uuid4()),
        "days": 30
    }
    response = client.post("/tickets/admin/activate-shop", json=payload)
    assert response.status_code == 401
    assert "X-Superadmin-Key" in response.json()["detail"]


def test_activate_shop_endpoint_invalid_key_returns_403():
    """Scenario: Wrong key returns 403 via HTTP call (TestClient)"""
    client = TestClient(app)
    payload = {
        "shop_id": str(uuid.uuid4()),
        "days": 30
    }
    headers = {"X-Superadmin-Key": "wrong-key-value"}
    response = client.post("/tickets/admin/activate-shop", json=payload, headers=headers)
    assert response.status_code == 403
    assert "inválida" in response.json()["detail"]
