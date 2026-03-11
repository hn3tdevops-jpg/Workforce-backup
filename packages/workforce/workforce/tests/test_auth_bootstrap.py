"""
Tests for POST /api/v1/auth/bootstrap.

Covers:
- 403 when ENABLE_BOOTSTRAP is False (default)
- 401 when ENABLE_BOOTSTRAP is True but token is missing or wrong
- 201 with superadmin created when settings are correct and no users exist
"""
import os

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-bootstrap-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch

from apps.api.app.models.base import Base
from apps.api.app.core.db import get_db
from apps.api.app.main import app

VALID_TOKEN = "test-bootstrap-token-xyz"


# ── Test DB setup ──────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture
def db_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture
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


# ── Helpers ────────────────────────────────────────────────────────────────────

def _post_bootstrap(client, token=None, payload=None):
    """POST /api/v1/auth/bootstrap with optional X-Bootstrap-Token header."""
    if payload is None:
        payload = {"email": "admin@example.com", "password": "SecurePass1!"}
    headers = {}
    if token is not None:
        headers["X-Bootstrap-Token"] = token
    return client.post("/api/v1/auth/bootstrap", json=payload, headers=headers)


# ── Tests ──────────────────────────────────────────────────────────────────────

def test_bootstrap_disabled_returns_403(client):
    """When ENABLE_BOOTSTRAP=False (default), endpoint returns 403."""
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = False
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r = _post_bootstrap(client, token=VALID_TOKEN)
    assert r.status_code == 403
    assert "Bootstrap disabled" in r.json()["detail"]


def test_bootstrap_missing_token_returns_401(client):
    """When ENABLE_BOOTSTRAP=True and no token provided, returns 401."""
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = True
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r = _post_bootstrap(client, token=None)
    assert r.status_code == 401


def test_bootstrap_wrong_token_returns_401(client):
    """When ENABLE_BOOTSTRAP=True and wrong token provided, returns 401."""
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = True
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r = _post_bootstrap(client, token="wrong-token")
    assert r.status_code == 401


def test_bootstrap_creates_superadmin_returns_201(client):
    """When ENABLE_BOOTSTRAP=True, correct token, and no users exist, creates superadmin."""
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = True
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r = _post_bootstrap(
            client,
            token=VALID_TOKEN,
            payload={
                "email": "superadmin@example.com",
                "password": "SecurePass1!",
                "first_name": "Super",
                "last_name": "Admin",
            },
        )
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "superadmin@example.com"
    assert "id" in data
    # token must NOT appear in the response
    assert VALID_TOKEN not in str(data)


def test_bootstrap_already_performed_returns_400(client):
    """When ENABLE_BOOTSTRAP=True and a user already exists, returns 400."""
    # Create the first superadmin
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = True
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r = _post_bootstrap(client, token=VALID_TOKEN)
    assert r.status_code == 201

    # Attempt bootstrap a second time
    with patch("app.api.v1.auth.bootstrap.settings") as mock_settings:
        mock_settings.ENABLE_BOOTSTRAP = True
        mock_settings.BOOTSTRAP_TOKEN = VALID_TOKEN
        r2 = _post_bootstrap(client, token=VALID_TOKEN)
    assert r2.status_code == 400
    assert "already" in r2.json()["detail"].lower()
