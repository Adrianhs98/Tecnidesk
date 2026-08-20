"""
Punto de entrada principal de la aplicación TecniDesk.
Configura FastAPI, CORS y registra todos los routers.
"""
import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.core.exceptions import EmbeddingServiceUnavailableError
from app.core.rate_limit import limiter
from app.routers import health, shops

settings = get_settings()



# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Acciones al iniciar y apagar la aplicación."""
    # Aquí se pueden añadir: verificar conexión a DB, calentar caché, etc.
    yield
    # Cleanup al apagar


# ─── Instancia FastAPI ────────────────────────────────────────────────────────
app = FastAPI(
    title="TecniDesk API",
    description="Backend para el Micro SaaS Multi-Tenant de gestión de talleres de reparación de celulares.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
# (Aquí seguro ya tienes tu app = FastAPI(...))

# ─── Rate Limiting & Exception Handlers ────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

logger = logging.getLogger("tecnidesk.main")


@app.exception_handler(EmbeddingServiceUnavailableError)
async def embedding_service_unavailable_handler(request: Request, exc: EmbeddingServiceUnavailableError):
    """Manejo de fallo de conectividad con el servicio local Ollama / Tailscale."""
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.message or "Local embedding service unavailable. Please check Tailscale Funnel / Mac mini Ollama status.",
            "code": "EMBEDDING_SERVICE_UNAVAILABLE",
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Atrapa errores 500 no controlados, genera un request_id y devuelve
    un JSONResponse para que el middleware de CORS pueda procesarlo y
    el navegador no oculte el error detrás de un mensaje de CORS genérico.
    """
    request_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception [req_id={request_id}] en {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor.",
            "request_id": request_id,
        }
    )

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Producción: solo subdominios de tecnidesk.lat y adriansaas.xyz (y dominios raíz)
_prod_regex = r"^https://(.*\.+)?(tecnidesk\.lat|adriansaas\.xyz)$"

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_prod_regex,
    allow_origins=settings.dev_origins + [settings.frontend_url.strip("/")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(shops.router)

# Fase 2.1 — Autenticación
from app.routers import auth  # noqa: E402
app.include_router(auth.router)

from app.routers import technicians  # noqa: E402
app.include_router(technicians.router)

# Fase 2.3 — Tickets (Órdenes de Reparación)
from app.routers import tickets  # noqa: E402
app.include_router(tickets.router)

from app.routers import inventory  # noqa: E402
app.include_router(inventory.router)

from app.routers import clients
app.include_router(clients.router)

# RUTAS PÚBLICAS — El antiguo /track fue reemplazado por /tracking (app/api/v1/)

from app.routers import test_verification
app.include_router(test_verification.router)

# Fase 4 — Portal tracking público
from app.api.v1.api import api_router as tracking_api_router
app.include_router(tracking_api_router)
