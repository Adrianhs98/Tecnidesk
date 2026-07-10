"""
Módulo de base de datos — sesión async y engine SQLAlchemy 2.0.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

# Engine async con pool de conexiones
engine = create_async_engine(
    settings.db_url,
    echo=False,          # Cambiar a True para debug SQL en desarrollo
    pool_pre_ping=True,  # Verifica conexiones antes de usarlas
    pool_size=3,        # C3: Reducido para free tier (e2-micro / Supabase / Neon)
    max_overflow=5,     # máximo 8 conexiones totales en pico
    connect_args={
        "server_settings": {"jit": "off"},
        "prepared_statement_cache_size": 0,
        "statement_cache_size": 0  # Desactiva el cache de statements para compatibilidad con PgBouncer en Supabase
    }
)

# Fábrica de sesiones async
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency de FastAPI — inyecta una sesión de BD por request.
    Hace rollback automático si ocurre una excepción no controlada.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
