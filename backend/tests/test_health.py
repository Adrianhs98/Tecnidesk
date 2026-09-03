"""Hermetic /health smoke test — no live DB, no bound socket."""

import httpx
import pytest


@pytest.mark.asyncio
async def test_health_returns_ok(test_app):
    transport = httpx.ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "TecniDesk API"
    # timestamp is dynamic — intentionally not asserted
