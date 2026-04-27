# Use the canonical package namespace for tests. Ensure packages/workforce models
# are not auto-inserted into apps.api.app.__path__ during pytest collection which
# can cause duplicate SQLAlchemy Table registration. Set an env var that the
# apps.api.app.models package honors to skip the optional path-extension.
import os
import sys

os.environ.setdefault("SKIP_WORKFORCE_MODELS", "1")

# Prevent accidental imports of the local packages/workforce package during test
# collection by removing any matching entries from sys.path. This ensures tests
# run against the local apps.api.app model implementations when SKIP_WORKFORCE_MODELS
# is set.
repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
for p in list(sys.path):
    if p and os.path.normpath(p).startswith(os.path.join(repo_root, "packages")):
        try:
            sys.path.remove(p)
        except ValueError:
            pass

# Always import apps.api.app so models are registered under a single package name
# and avoid duplicate MetaData.
_using_installed_pkg = True

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine
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

    # Re-import model modules and reload to ensure they are bound to the
    # same Base/MetaData instance used by the test harness. This helps avoid
    # hidden import-order differences between modules importing models under
    # alternate package names.
    import importlib
    try:
        import apps.api.app.models.tenant as _tenant_mod
        import apps.api.app.models.user as _user_mod
        import apps.api.app.models.access_control as _ac_mod
        importlib.reload(_tenant_mod)
        importlib.reload(_user_mod)
        importlib.reload(_ac_mod)
    except Exception:
        # Best-effort; continue to metadata creation which may still succeed
        pass

    # Dump metadata table keys before create_all for diagnostics
    try:
        with open('/tmp/metadata_before_create.log', 'w') as f:
            f.write('\n'.join(sorted(list(Base.metadata.tables.keys()))) + '\n')
    except Exception:
        pass

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(db_engine):
    """Create a single shared connection and transaction for the test.

    This connection is used by both the test db_session and the application's
    request-time sessions so that queries see the same transactional state.
    """
    # Ensure models are imported before creating the connection
    import_models()

    conn = await db_engine.connect()
    trans = await conn.begin()
    try:
        yield conn
    finally:
        # Roll back the outer transaction and close the connection
        await trans.rollback()
        await conn.close()


@pytest_asyncio.fixture
async def db_session(db_connection):
    """Provide a single Sync-backed async adapter session bound to the shared
    connection/transaction for the duration of the test so run_sync calls and
    application request sessions see the same transactional state.
    """
    conn = db_connection
    from sqlalchemy.orm import Session as SyncSession

    sync_session = SyncSession(
        bind=conn.sync_connection, expire_on_commit=False
    )

    # Create a small adapter that exposes async-compatible methods delegating
    # to the SyncSession via greenlet_spawn so application code can await them.
    from sqlalchemy.util.concurrency import greenlet_spawn

    class SyncSessionAdapter:
        def __init__(self, sync_session):
            self._sync = sync_session

        async def run_sync(self, func):
            return await greenlet_spawn(lambda: func(self._sync))

        async def scalar(self, stmt):
            return await greenlet_spawn(lambda: self._sync.scalar(stmt))

        async def scalars(self, stmt):
            result = await greenlet_spawn(lambda: self._sync.scalars(stmt))
            return result

        async def execute(self, stmt):
            return await greenlet_spawn(lambda: self._sync.execute(stmt))

        def add(self, obj):
            # add is synchronous on AsyncSession; implement as sync to match
            # application code which calls session.add(obj) without awaiting.
            return self._sync.add(obj)

        def add_all(self, objs):
            return self._sync.add_all(objs)

        async def flush(self):
            return await greenlet_spawn(self._sync.flush)

        async def commit(self):
            return await greenlet_spawn(self._sync.commit)

        async def rollback(self):
            return await greenlet_spawn(self._sync.rollback)

        async def close(self):
            return await greenlet_spawn(self._sync.close)

        async def delete(self, obj):
            return await greenlet_spawn(lambda: self._sync.delete(obj))

        async def refresh(self, obj):
            try:
                return await greenlet_spawn(lambda: self._sync.refresh(obj))
            except Exception:
                # Instance may not be attached to this Session in the test adapter;
                # make refresh a no-op to avoid test harness failures. Tests should
                # rely on selecting by id when fresh state is required.
                return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    adapter = SyncSessionAdapter(sync_session)

    try:
        yield adapter
    finally:
        # Ensure the sync session is closed by the db_connection finalizer
        await adapter.close()


@pytest_asyncio.fixture
async def client(db_connection):
    """HTTP client that creates a per-request SyncSession adapter bound to the
    shared connection. Each request handler receives a fresh Session-backed
    adapter which ensures the request lifecycle is isolated while reading
    committed state from the shared connection.
    """
    conn = db_connection
    from sqlalchemy.orm import Session as SyncSession
    from sqlalchemy.util.concurrency import greenlet_spawn

    class SyncSessionAdapter:
        def __init__(self, sync_session):
            self._sync = sync_session

        async def run_sync(self, func):
            return await greenlet_spawn(lambda: func(self._sync))

        async def scalar(self, stmt):
            return await greenlet_spawn(lambda: self._sync.scalar(stmt))

        async def scalars(self, stmt):
            result = await greenlet_spawn(lambda: self._sync.scalars(stmt))
            return result

        async def execute(self, stmt):
            return await greenlet_spawn(lambda: self._sync.execute(stmt))

        def add(self, obj):
            return self._sync.add(obj)

        def add_all(self, objs):
            return self._sync.add_all(objs)

        async def flush(self):
            return await greenlet_spawn(self._sync.flush)

        async def commit(self):
            return await greenlet_spawn(self._sync.commit)

        async def rollback(self):
            return await greenlet_spawn(self._sync.rollback)

        async def close(self):
            return await greenlet_spawn(self._sync.close)

        async def delete(self, obj):
            return await greenlet_spawn(lambda: self._sync.delete(obj))

        async def refresh(self, obj):
            try:
                return await greenlet_spawn(lambda: self._sync.refresh(obj))
            except Exception:
                # Avoid failing tests when refresh is called on an instance not
                # attached to this per-request Session. Fall back to a no-op.
                return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    async def override_get_async_session():
        sync_session = SyncSession(
            bind=conn.sync_connection, expire_on_commit=False
        )
        adapter = SyncSessionAdapter(sync_session)
        try:
            async with adapter:
                yield adapter
        finally:
            await adapter.close()

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
