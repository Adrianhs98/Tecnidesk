"""Pytest bootstrap: seed required env vars BEFORE importing the app.

Settings.get_settings() runs at `app.main` import time and validation fails
without db_url / jwt_secret / jwt_refresh_secret / fernet_key. pytest loads
conftest.py before any test module, so the env is guaranteed to be set before
test_health.py imports `app`. The dummy db_url is NEVER dialed: create_async_engine
does not connect at import time and /health is DB-free.
"""

import base64
import os

os.environ.setdefault("db_url", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("jwt_secret", "T" * 64)
os.environ.setdefault("jwt_refresh_secret", "R" * 64)
os.environ.setdefault("fernet_key", base64.urlsafe_b64encode(b"a" * 32).decode())

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import app  # noqa: E402 (import after env seeding, by design)
from app.database import get_db
from app.config import get_settings


@pytest.fixture
def test_app():
    """Expose the env-seeded FastAPI app to test modules."""
    return app


@pytest_asyncio.fixture
async def db_engine():
    """Fixture to provide the SQLAlchemy engine with NullPool."""
    settings = get_settings()
    engine = create_async_engine(
        settings.db_url,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()
