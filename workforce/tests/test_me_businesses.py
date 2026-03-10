import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.business import Business
from app.models.identity import User, Membership, MembershipStatus
from app.core.db import get_db
from app.core.security import create_access_token
from app.main import app


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


@pytest.fixture(scope="module")
def db_factory(engine):
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal


@pytest.fixture(scope="module")
def setup_data(engine, db_factory):
    db = db_factory()
    biz = Business(name="Test Biz")
    db.add(biz)
    db.flush()

    user = User(email="me@test.com", hashed_password="x", is_superadmin=False)
    db.add(user)
    db.flush()

    mem = Membership(user_id=user.id, business_id=biz.id, status=MembershipStatus.active)
    db.add(mem)
    db.commit()

    token = create_access_token(user.id)
    return {"biz_id": biz.id, "user_id": user.id, "token": token}


@pytest.fixture(scope="module")
def client(engine, db_factory):
    import app.core.db as _db_module
    from app.models.base import Base as _Base

    orig_engine = _db_module.engine
    orig_session = _db_module.SessionLocal
    _db_module.engine = engine
    _db_module.SessionLocal = db_factory
    _Base.metadata.create_all(engine)

    def override_get_db():
        db = db_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    _db_module.engine = orig_engine
    _db_module.SessionLocal = orig_session


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_my_businesses_returns_business_for_user(client, setup_data):
    r = client.get("/api/v1/me/businesses", headers=auth(setup_data["token"]))
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(b["name"] == "Test Biz" for b in data)


def test_my_businesses_requires_auth(client):
    r = client.get("/api/v1/me/businesses")
    assert r.status_code == 401
