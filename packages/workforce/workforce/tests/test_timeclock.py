"""
Timeclock API tests: clock-in, clock-out, double clock-in prevention,
timecards rollup, admin correction endpoint.
Uses in-memory SQLite.
"""
import os
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.app.models.base import Base
from apps.api.app.models.business import Business, Location
from apps.api.app.models.identity import (
    User, Membership, MembershipStatus, UserStatus,
    BizRole, BizRolePermission, MembershipRole, Permission,
)
from apps.api.app.core.security import create_access_token
from apps.api.app.core.db import get_db
from apps.api.app.main import app


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
def setup_data(engine, db_factory):
    db = db_factory()

    biz = Business(name="Clock Hotel")
    db.add(biz)
    db.flush()

    loc = Location(business_id=biz.id, name="Front Desk", timezone="UTC")
    db.add(loc)
    db.flush()

    worker = User(email="clocker@test.com", hashed_password="x",
                  is_superadmin=False, status=UserStatus.active)
    manager = User(email="clock-mgr@test.com", hashed_password="x",
                   is_superadmin=False, status=UserStatus.active)
    db.add_all([worker, manager])
    db.flush()

    # Manager gets timeclock:manage permission
    perm = Permission(key="timeclock:manage", description="Manage timeclock")
    db.add(perm)
    db.flush()

    role = BizRole(business_id=biz.id, name="Clock Manager")
    db.add(role)
    db.flush()
    db.add(BizRolePermission(role_id=role.id, permission_id=perm.id))

    w_mem  = Membership(user_id=worker.id,  business_id=biz.id, status=MembershipStatus.active)
    m_mem  = Membership(user_id=manager.id, business_id=biz.id, status=MembershipStatus.active)
    db.add_all([w_mem, m_mem])
    db.flush()
    db.add(MembershipRole(membership_id=m_mem.id, role_id=role.id))
    db.commit()

    return {
        "biz_id": biz.id,
        "loc_id": loc.id,
        "worker_id": worker.id,
        "manager_id": manager.id,
        "w_token": create_access_token(worker.id, business_id=biz.id),
        "m_token": create_access_token(manager.id, business_id=biz.id),
    }


@pytest.fixture(scope="module")
def client(engine, db_factory):
    import apps.api.app.core.db as _db_module
    from apps.api.app.models.base import Base as _Base

    orig_engine  = _db_module.engine
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
    yield TestClient(app, raise_server_exceptions=True)
    app.dependency_overrides.pop(get_db, None)
    _db_module.engine = orig_engine
    _db_module.SessionLocal = orig_session


def auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Clock-in / clock-out ──────────────────────────────────────────────────────

def test_clock_in(client, setup_data):
    biz = setup_data["biz_id"]
    r = client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-in",
        json={"location_id": setup_data["loc_id"]},
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 201
    body = r.json()
    assert body["clocked_out_at"] is None
    assert body["status"] == "active"


def test_double_clock_in_rejected(client, setup_data):
    """Cannot clock in while already clocked in."""
    biz = setup_data["biz_id"]
    r = client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-in",
        json={},
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 409


def test_clock_out(client, setup_data):
    biz = setup_data["biz_id"]
    r = client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-out",
        json={"notes": "Done for today"},
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["clocked_out_at"] is not None
    assert body["total_minutes"] is not None
    assert body["status"] == "completed"


def test_clock_out_when_not_in_returns_404(client, setup_data):
    biz = setup_data["biz_id"]
    r = client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-out",
        json={},
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 404


def test_clock_status_endpoint(client, setup_data):
    biz = setup_data["biz_id"]
    r = client.get(
        f"/api/v1/worker/me/timeclock/{biz}/status",
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 200
    assert r.json()["clocked_in"] is False
    assert r.json()["can_clock_in"] is True


def test_clock_in_then_status_shows_active(client, setup_data):
    biz = setup_data["biz_id"]
    client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-in",
        json={},
        headers=auth(setup_data["w_token"]),
    )
    r = client.get(
        f"/api/v1/worker/me/timeclock/{biz}/status",
        headers=auth(setup_data["w_token"]),
    )
    assert r.json()["clocked_in"] is True
    assert r.json()["entry"] is not None

    # Clean up
    client.post(
        f"/api/v1/worker/me/timeclock/{biz}/clock-out",
        json={},
        headers=auth(setup_data["w_token"]),
    )


# ── Timecards rollup ──────────────────────────────────────────────────────────

def test_timecards_rollup(client, setup_data):
    """Timecards endpoint rolls up completed entries by user."""
    biz = setup_data["biz_id"]
    # Clock in and out to generate a completed entry
    client.post(f"/api/v1/worker/me/timeclock/{biz}/clock-in", json={},
                headers=auth(setup_data["w_token"]))
    client.post(f"/api/v1/worker/me/timeclock/{biz}/clock-out", json={},
                headers=auth(setup_data["w_token"]))

    r = client.get(
        f"/api/v1/tenant/{biz}/timeclock/timecards",
        params={"start": "2020-01-01", "end": "2030-12-31"},
        headers=auth(setup_data["m_token"]),
    )
    assert r.status_code == 200
    body = r.json()
    assert "timecards" in body
    user_ids = [tc["user_id"] for tc in body["timecards"]]
    assert setup_data["worker_id"] in user_ids
    # Each timecard has by_day breakdown
    for tc in body["timecards"]:
        assert "total_seconds" in tc
        assert "by_day" in tc


# ── Admin correction ──────────────────────────────────────────────────────────

def test_admin_correction_entry(client, setup_data, db_factory):
    """PATCH /tenant/{biz}/timeclock/{entry_id} updates status and writes audit."""
    from apps.api.app.models.timeclock import TimeEntry, TimeEntryStatus

    biz = setup_data["biz_id"]

    # Create a completed entry directly
    db = db_factory()
    from datetime import datetime, timezone, timedelta
    cin = datetime.now(timezone.utc) - timedelta(hours=2)
    cout = datetime.now(timezone.utc) - timedelta(hours=1)
    entry = TimeEntry(
        user_id=setup_data["worker_id"],
        business_id=biz,
        location_id=None,
        clocked_in_at=cin,
        clocked_out_at=cout,
        total_minutes=60.0,
        status=TimeEntryStatus.completed,
    )
    db.add(entry)
    db.commit()
    entry_id = entry.id
    db.close()

    r = client.patch(
        f"/api/v1/tenant/{biz}/timeclock/{entry_id}",
        json={"status": "approved", "notes": "Reviewed by manager"},
        headers=auth(setup_data["m_token"]),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "approved"


def test_admin_correction_requires_permission(client, setup_data):
    """Worker without timeclock:manage cannot correct entries."""
    biz = setup_data["biz_id"]
    r = client.patch(
        f"/api/v1/tenant/{biz}/timeclock/nonexistent-id",
        json={"status": "approved"},
        headers=auth(setup_data["w_token"]),
    )
    assert r.status_code == 403


def test_timeclock_status_for_user_service_endpoint(client, setup_data):
    """Manager can query timeclock status for any user (service-to-service endpoint)."""
    biz = setup_data["biz_id"]
    r = client.get(
        f"/api/v1/tenant/{biz}/timeclock/status/{setup_data['worker_id']}",
        headers=auth(setup_data["m_token"]),
    )
    assert r.status_code == 200
    assert "clocked_in" in r.json()
    assert r.json()["user_id"] == setup_data["worker_id"]
