"""
Phase 2 auth tests: /token, /refresh, /logout endpoints,
decode_token alias, passlib CryptContext, and auth models.
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-phase2-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.core.db import get_db
from app.main import app


# ── Test DB setup ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="module")
def db_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(scope="module")
def client(engine, db_factory):
    def override_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Security utilities ────────────────────────────────────────────────────────

def test_pwd_context_available():
    from app.core.security import pwd_context
    hashed = pwd_context.hash("mypassword")
    assert pwd_context.verify("mypassword", hashed)


def test_decode_token_alias():
    from app.core.security import create_access_token, decode_token
    token = create_access_token("user-abc")
    payload = decode_token(token)
    assert payload["sub"] == "user-abc"
    assert payload["type"] == "access"


def test_create_access_token_with_data_kwarg():
    from app.core.security import create_access_token, decode_token
    from datetime import timedelta

    token = create_access_token(
        "ignored",
        data={"sub": "user-xyz", "email": "x@example.com"},
        expires_delta=timedelta(minutes=30),
    )
    payload = decode_token(token)
    assert payload["sub"] == "user-xyz"
    assert payload["email"] == "x@example.com"
    assert payload["type"] == "access"


# ── Config ────────────────────────────────────────────────────────────────────

def test_get_settings():
    from app.core.config import get_settings
    s = get_settings()
    assert s.ACCESS_TOKEN_EXPIRE_MINUTES == 15
    assert s.REFRESH_TOKEN_EXPIRE_DAYS == 7


# ── Auth models ───────────────────────────────────────────────────────────────

def test_role_importable_from_auth():
    from app.models.auth import Role
    assert Role.__tablename__ == "roles"


def test_user_roles_table_importable():
    from app.models.auth import user_roles
    assert "user_id" in [c.name for c in user_roles.columns]
    assert "role_id" in [c.name for c in user_roles.columns]


def test_refresh_token_re_exported():
    from app.models.auth import RefreshToken
    assert RefreshToken.__tablename__ == "refresh_tokens"


# ── db.base ───────────────────────────────────────────────────────────────────

def test_import_models():
    from app.db.base import import_models
    import_models()  # must not raise


# ── deps.py ───────────────────────────────────────────────────────────────────

def test_get_current_user_importable():
    from app.api.deps import get_current_user
    assert callable(get_current_user)


# ── Auth endpoints ────────────────────────────────────────────────────────────

def test_token_invalid_credentials(client):
    r = client.post("/api/v1/auth/token", json={"email": "nobody@x.com", "password": "wrong"})
    assert r.status_code == 401


def test_register_and_token(client):
    # Register a new user
    r = client.post("/api/v1/auth/register", json={"email": "phase2@example.com", "password": "Pass123!"})
    assert r.status_code == 201

    # Obtain tokens via /token
    r = client.post("/api/v1/auth/token", json={"email": "phase2@example.com", "password": "Pass123!"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 15 * 60


def test_refresh_token(client):
    # Register fresh user
    client.post("/api/v1/auth/register", json={"email": "refresh2@example.com", "password": "Pass123!"})
    r = client.post("/api/v1/auth/token", json={"email": "refresh2@example.com", "password": "Pass123!"})
    tokens = r.json()

    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 200
    new_tokens = r2.json()
    assert "access_token" in new_tokens
    # Old refresh token should now be revoked
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 401


def test_logout(client):
    client.post("/api/v1/auth/register", json={"email": "logout2@example.com", "password": "Pass123!"})
    r = client.post("/api/v1/auth/token", json={"email": "logout2@example.com", "password": "Pass123!"})
    tokens = r.json()

    r2 = client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert r2.status_code == 200

    # Token should be revoked now
    r3 = client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r3.status_code == 401


def test_logout_unknown_token(client):
    r = client.post("/api/v1/auth/logout", json={"refresh_token": "nonexistent-token"})
    assert r.status_code == 200  # idempotent — no error on unknown token


# ── api/routes/auth.py re-export ──────────────────────────────────────────────

def test_routes_auth_re_export():
    from app.api.routes.auth import router
    paths = {r.path for r in router.routes}
    assert "/api/v1/auth/token" in paths
    assert "/api/v1/auth/logout" in paths
