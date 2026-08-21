import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_invalid_tracking_token_returns_422():
    response = client.get("/tracking/invalid-token-123")
    assert response.status_code == 422

def test_invalid_tracking_token_approve_returns_422():
    response = client.post("/tracking/invalid-token-123/approve")
    assert response.status_code == 422

def test_invalid_tracking_token_reject_returns_422():
    response = client.post("/tracking/invalid-token-123/reject")
    assert response.status_code == 422
