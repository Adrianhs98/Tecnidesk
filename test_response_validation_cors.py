import pytest
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"error": "my_handler"}, headers={"Access-Control-Allow-Origin": "http://localhost"})

from pydantic import BaseModel

class Out(BaseModel):
    name: str

@app.patch("/test_response_validation", response_model=Out)
def test_response_validation():
    return {"wrong_key": "data"}

@pytest.mark.asyncio
async def test_response_validation_cors():
    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.patch("/test_response_validation", headers={"Origin": "http://localhost"})
        print("Status:", r.status_code)
        print("Headers:", r.headers)
