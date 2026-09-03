import pytest

@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    response = await client.get("/health")
    # Health endpoints usually return 200
    assert response.status_code == 200
