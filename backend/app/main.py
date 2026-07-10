"""
Punto de entrada principal de la aplicación TecniDesk.
Configura FastAPI, CORS y registra todos los routers.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
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

# ─── Rate Limiting ────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# ─── CORS ─────────────────────────────────────────────────────────────────────
# Producción: solo subdominios de adriansaas.xyz
# Desarrollo: orígenes adicionales desde ALLOWED_ORIGINS_DEV
_prod_regex = r"^https://.*\.adriansaas\.xyz$"

app.add_middleware(
    CORSMiddleware,
    # allow_origin_regex cubre *.adriansaas.xyz sin wildcard literal
    allow_origin_regex=_prod_regex,
    # Orígenes concretos para desarrollo local (vacío en producción)
    allow_origins=settings.dev_origins,
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

# Fase 2.3 — Tickets (Órdenes de Reparación)
from app.routers import tickets  # noqa: E402
app.include_router(tickets.router)

# RUTAS PÚBLICAS — El antiguo /track fue reemplazado por /tracking (app/api/v1/)

from app.routers import test_verification
app.include_router(test_verification.router)

# Fase 4 — Portal tracking público
from app.api.v1.api import api_router as tracking_api_router
app.include_router(tracking_api_router)
