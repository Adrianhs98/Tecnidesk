import pytest
import httpx
from fastapi import Request
from fastapi.responses import JSONResponse
import uuid

from app.main import app

@app.get("/_test_crash")
def intentional_crash():
    raise ValueError("Intentional crash for testing CORS on 500 errors")

@pytest.mark.asyncio
async def test_500_error_contains_cors_headers():
    """
    Ensure that when an unhandled exception occurs and is caught by the global_exception_handler,
    the response still includes the correct CORS headers so the browser doesn't swallow the 500 error.
    """
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/_test_crash", headers={"Origin": "https://tenant.tecnidesk.lat"})
        
        # Verify it returns 500
        assert response.status_code == 500
        
        # Verify it has CORS headers matching the origin (from our manual injection)
        assert response.headers.get("access-control-allow-origin") == "https://tenant.tecnidesk.lat"
        assert response.headers.get("access-control-allow-credentials") == "true"
        
        # Verify body
        data = response.json()
        assert "Internal server error" in data["detail"]
        assert data["error_type"] == "ValueError"

@pytest.mark.asyncio
async def test_500_error_no_cors_for_invalid_origin():
    """
    Ensure that invalid origins do NOT get the CORS headers.
    """
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/_test_crash", headers={"Origin": "https://evil-hacker.com"})
        
        # Verify it returns 500
        assert response.status_code == 500
        
        # Verify NO CORS headers are attached
        assert "access-control-allow-origin" not in response.headers
