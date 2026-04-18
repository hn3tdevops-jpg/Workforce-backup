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
    """Provide a single AsyncSession bound to the same connection/transaction
    for the duration of the test so run_sync calls see the same uncommitted
    state across multiple lambda calls.
    """
    # Create a connection and begin a nested transaction that will be rolled back
    # after the test. Bind the AsyncSession to the same connection so all
    # run_sync() calls operate on the same transactional state.
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        # Create a synchronous Session bound to the same underlying connection
        # so run_sync calls can reuse a single identity map across calls.
        from sqlalchemy.orm import Session as SyncSession
        sync_session = SyncSession(bind=conn.sync_connection)

        async with AsyncSession(bind=conn, expire_on_commit=False, autoflush=False) as session:
            # Override run_sync on this AsyncSession instance so all run_sync
            # invocations reuse the same SyncSession (identity map visible).
            from sqlalchemy.util.concurrency import greenlet_spawn

            async def _single_run_sync(func):
                # Run the provided synchronous callable inside a greenlet so
                # SQLAlchemy's sync-to-async bridging (await_only) works.
                return await greenlet_spawn(lambda: func(sync_session))

            session.run_sync = _single_run_sync

            # Ensure commits/rollbacks operate on the same SyncSession so that
            # objects added via run_sync are persisted by db_session.commit().
            async def _commit():
                await greenlet_spawn(sync_session.commit)

            async def _rollback():
                await greenlet_spawn(sync_session.rollback)

            async def _close():
                await greenlet_spawn(sync_session.close)

            session.commit = _commit
            session.rollback = _rollback
            session.close = _close

            try:
                yield session
            finally:
                # close sync session and rollback the transaction
                await session.close()
                await trans.rollback()


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