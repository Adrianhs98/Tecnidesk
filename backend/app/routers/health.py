"""
Router: GET /health — Endpoint de salud de la aplicación.
Accesible sin autenticación. Devuelve 200 OK con timestamp UTC.
"""
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


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
    return {
        "status": "ok",
        "service": "TecniDesk API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
