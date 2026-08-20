"""
Router: GET /health — Endpoint de salud de la aplicación.
Accesible sin autenticación. Devuelve 200 OK con timestamp UTC.
"""
from datetime import datetime, timezone
import time

from fastapi import APIRouter

router = APIRouter(tags=["health"])

START_TIME = time.time()


@router.get(
    "/health",
    summary="Health Check",
    description="Verifica que la aplicación esté corriendo correctamente.",
)
async def health_check() -> dict:
    """
    Smoke test ST-01/ST-02.
    Devuelve 200 OK con timestamp UTC.
    """
    uptime = round(time.time() - START_TIME, 2)
    return {
        "status": "ok",
        "service": "TecniDesk API",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
