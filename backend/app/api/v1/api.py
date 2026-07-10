from fastapi import APIRouter

from app.api.v1.endpoints import tracking

api_router = APIRouter()

api_router.include_router(tracking.router, prefix="/tracking", tags=["Tracking Público"])
