import sys
import pathlib

# Use the canonical package namespace for tests. Ensure packages/workforce models
# are not auto-inserted into apps.api.app.__path__ during pytest collection which
# can cause duplicate SQLAlchemy Table registration. Set an env var that the
# apps.api.app.models package honors to skip the optional path-extension.
import os
os.environ.setdefault("SKIP_WORKFORCE_MODELS", "1")

# Always import apps.api.app so models are registered under a single package name
# and avoid duplicate MetaData.
import apps.api.app  # ensure package is importable
_using_installed_pkg = True

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from apps.api.app.db.base import Base, import_models

# Ensure core app models are imported and registered early to avoid duplicate
# SQLAlchemy Table registration when tests import model modules during collection.
import_models()

from apps.api.app.db.session import get_async_session
# Import the FastAPI app lazily inside the client fixture so tests control when models
# are imported/registered and avoid duplicate SQLAlchemy table definitions.
# from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_engine():
    import_models()

    engine = create_async_engine(
        TEST_DATABASE_URL,
        future=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    AsyncTestSession = async_sessionmaker(
        bind=db_engine,
        class_=AsyncSession,
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
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    async def override_get_async_session():
        async with AsyncTestSession() as session:
            yield session

    # Import app after DB models are registered so the application doesn't import
    # endpoints (and thereby models) before the test fixture has prepared the DB.
    from apps.api.app.main import app  # local import

    app.dependency_overrides[get_async_session] = override_get_async_session

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()