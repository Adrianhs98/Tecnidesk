import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.main import app
from app.database import get_db, engine as prod_engine

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Fixture to provide the SQLAlchemy engine."""
    yield prod_engine

@pytest_asyncio.fixture
async def db_session(db_engine):
    """
    Fixture for SQLAlchemy session with transaction rollback.
    Creates a nested transaction that is rolled back after each test.
    """
    connection = await db_engine.connect()
    # Begin a non-ORM transaction
    transaction = await connection.begin()
    
    # Bind session to the connection
    AsyncSessionLocal = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    session = AsyncSessionLocal()
    
    # Create a savepoint
    await connection.begin_nested() 

    try:
        yield session
    finally:
        await session.close()
        # Rollback the overall transaction, restoring the state
        await transaction.rollback()
        await connection.close()

@pytest_asyncio.fixture
async def client(db_session):
    """
    Async HTTP client fixture with overridden get_db dependency.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
        
    app.dependency_overrides.clear()
