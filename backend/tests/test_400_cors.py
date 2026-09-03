import pytest
import httpx
from fastapi import Request, HTTPException
from app.main import app

@app.patch("/_test_400")
def intentional_400():
    raise HTTPException(status_code=400, detail="Intentional 400")

@pytest.mark.asyncio
async def test_400_error_cors():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.patch("/_test_400", headers={"Origin": "https://tenant.tecnidesk.lat"})
        print("400 Response headers:", response.headers)
