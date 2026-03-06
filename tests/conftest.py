import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db.base import Base, import_models
from app.db.session import get_async_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    import_models()
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    AsyncTestSession = async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with AsyncTestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine):
    AsyncTestSession = async_sessionmaker(
        bind=db_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async def override_get_async_session():
        async with AsyncTestSession() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
