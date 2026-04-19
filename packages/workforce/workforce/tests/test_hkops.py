"""
HKops tests — rooms, task types, tasks, inspections, audit trail.
Uses in-memory SQLite via TestClient with overridden DB dependency.
"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "sqlite://")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from apps.api.app.models.base import Base
from apps.api.app.models.business import Business, Location
from apps.api.app.models.identity import (
    User, Membership, MembershipStatus, UserStatus,
    BizRole, BizRolePermission, MembershipRole, Permission,
)
from apps.api.app.models.hkops import (
    HKTask, TaskStatus,
)
from apps.api.app.core.security import create_access_token
from apps.api.app.core.db import get_db
from apps.api.app.main import app


# ── Fixtures ──────────────────────────────────────────────────────────────────

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
    """Create a business, location, owner user, worker user, and memberships."""
    db: Session = db_factory()

    biz = Business(name="Test Hotel")
    db.add(biz)
    db.flush()

    loc = Location(business_id=biz.id, name="Main Building", timezone="UTC")
    db.add(loc)
    db.flush()

    owner = User(email="hk-owner@test.com", hashed_password="x",
                 is_superadmin=False, status=UserStatus.active)
    worker = User(email="hk-worker@test.com", hashed_password="x",
                  is_superadmin=False, status=UserStatus.active)
    db.add_all([owner, worker])
    db.flush()

    # Give owner hkops permissions
    perm_manage = Permission(key="hkops:manage", description="HKops manage")
    perm_read   = Permission(key="hkops:read",   description="HKops read")
    db.add_all([perm_manage, perm_read])
    db.flush()

    role = BizRole(business_id=biz.id, name="HK Manager")
    db.add(role)
    db.flush()

    db.add_all([
        BizRolePermission(role_id=role.id, permission_id=perm_manage.id),
        BizRolePermission(role_id=role.id, permission_id=perm_read.id),
    ])

    owner_mem = Membership(user_id=owner.id, business_id=biz.id, status=MembershipStatus.active)
    worker_mem = Membership(user_id=worker.id, business_id=biz.id, status=MembershipStatus.active)
    db.add_all([owner_mem, worker_mem])
    db.flush()

    db.add(MembershipRole(membership_id=owner_mem.id, role_id=role.id))
    db.commit()

    return {
        "biz_id": biz.id, "loc_id": loc.id,
        "owner_id": owner.id, "worker_id": worker.id,
        "owner_token": create_access_token(owner.id),
        "worker_token": create_access_token(worker.id),
    }


@pytest.fixture(scope="module")
def client(engine, db_factory):
    """Patch app.core.db to use test engine, then create TestClient."""
    import apps.api.app.core.db as _db_module
    from apps.api.app.models.base import Base as _Base

    # Point the app's own engine and session factory at the test in-memory DB
    orig_engine = _db_module.engine
    orig_session = _db_module.SessionLocal
    _db_module.engine = engine
    _db_module.SessionLocal = db_factory
    # Ensure all tables exist in test engine (create_all is idempotent)
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


# ── Tests: Rooms ──────────────────────────────────────────────────────────────

def test_create_room(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.post(
        f"/api/v1/tenant/{biz}/hkops/rooms",
        json={"room_number": "101", "floor": "1", "wing": "East", "room_type": "Standard"},
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["room_number"] == "101"
    assert data["status"] == "dirty"  # default
    setup_data["room_id"] = data["id"]


def test_list_rooms(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/rooms",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_update_room_status(client, setup_data):
    biz = setup_data["biz_id"]
    rid = setup_data["room_id"]
    resp = client.patch(
        f"/api/v1/tenant/{biz}/hkops/rooms/{rid}",
        json={"status": "clean", "notes": "Cleaned by test"},
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "clean"


def test_get_room(client, setup_data):
    biz = setup_data["biz_id"]
    rid = setup_data["room_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/rooms/{rid}",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == rid


# ── Tests: Task Types ─────────────────────────────────────────────────────────

def test_create_task_type(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.post(
        f"/api/v1/tenant/{biz}/hkops/task-types",
        json={"name": "Checkout Clean", "default_duration_minutes": 45, "requires_inspection": True},
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Checkout Clean"
    assert data["requires_inspection"] is True
    setup_data["task_type_id"] = data["id"]


def test_list_task_types(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/task-types",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Tests: Tasks ──────────────────────────────────────────────────────────────

def test_create_task(client, setup_data):
    biz = setup_data["biz_id"]
    # Reset room to dirty first
    client.patch(
        f"/api/v1/tenant/{biz}/hkops/rooms/{setup_data['room_id']}",
        json={"status": "dirty"},
        headers=auth(setup_data["owner_token"]),
    )
    resp = client.post(
        f"/api/v1/tenant/{biz}/hkops/tasks",
        json={
            "room_id": setup_data["room_id"],
            "task_type_id": setup_data["task_type_id"],
            "assigned_to": setup_data["worker_id"],
            "priority": "high",
            "scheduled_date": "2026-03-01",
            "scheduled_start": "09:00",
            "scheduled_end": "09:45",
        },
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["assigned_to"] == setup_data["worker_id"]
    assert data["priority"] == "high"
    setup_data["task_id"] = data["id"]


def test_list_tasks(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/tasks",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_assign_task(client, setup_data):
    biz = setup_data["biz_id"]
    tid = setup_data["task_id"]
    resp = client.patch(
        f"/api/v1/tenant/{biz}/hkops/tasks/{tid}/assign",
        json={"priority": "urgent", "supervisor_notes": "Rush — checkout by 10am"},
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["priority"] == "urgent"


# ── Tests: Worker plane ───────────────────────────────────────────────────────

def test_worker_sees_tasks(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/worker/me/hkops/{biz}/tasks",
        headers=auth(setup_data["worker_token"]),
    )
    assert resp.status_code == 200
    tasks = resp.json()
    assert any(t["id"] == setup_data["task_id"] for t in tasks)


def test_worker_start_task(client, setup_data):
    biz = setup_data["biz_id"]
    tid = setup_data["task_id"]
    resp = client.patch(
        f"/api/v1/worker/me/hkops/{biz}/tasks/{tid}/status",
        json={"status": "in_progress"},
        headers=auth(setup_data["worker_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"
    assert resp.json()["started_at"] is not None


def test_worker_complete_task(client, setup_data):
    biz = setup_data["biz_id"]
    tid = setup_data["task_id"]
    resp = client.patch(
        f"/api/v1/worker/me/hkops/{biz}/tasks/{tid}/status",
        json={"status": "completed", "notes": "All done, fresh towels placed."},
        headers=auth(setup_data["worker_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "completed"
    assert data["completed_at"] is not None
    # Room should NOT be auto-marked clean because task_type requires_inspection=True


# ── Tests: Inspections ────────────────────────────────────────────────────────

def test_create_inspection_pass(client, setup_data):
    biz = setup_data["biz_id"]
    tid = setup_data["task_id"]
    resp = client.post(
        f"/api/v1/tenant/{biz}/hkops/inspections",
        json={
            "task_id": tid,
            "result": "pass",
            "score": 95,
            "issues": [],
            "notes": "Excellent work.",
        },
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["result"] == "pass"
    assert data["score"] == 95
    setup_data["inspection_id"] = data["id"]

    # Room should now be "inspected"
    room_resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/rooms/{setup_data['room_id']}",
        headers=auth(setup_data["owner_token"]),
    )
    assert room_resp.json()["status"] == "inspected"


def test_duplicate_inspection_rejected(client, setup_data):
    biz = setup_data["biz_id"]
    tid = setup_data["task_id"]
    resp = client.post(
        f"/api/v1/tenant/{biz}/hkops/inspections",
        json={"task_id": tid, "result": "fail"},
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 409


def test_list_inspections(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/inspections",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


# ── Tests: Summary ────────────────────────────────────────────────────────────

def test_room_board_summary(client, setup_data):
    biz = setup_data["biz_id"]
    resp = client.get(
        f"/api/v1/tenant/{biz}/hkops/summary",
        headers=auth(setup_data["owner_token"]),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "rooms" in data
    assert "tasks" in data


# ── Tests: Worker cannot access other worker's task ───────────────────────────

def test_worker_cannot_access_unassigned_task(client, setup_data, engine, db_factory):
    """Create a task for owner only, then try to fetch as worker."""
    biz = setup_data["biz_id"]
    db = db_factory()
    task2 = HKTask(
        business_id=biz,
        room_id=setup_data["room_id"],
        task_type_id=setup_data["task_type_id"],
        created_by=setup_data["owner_id"],
        assigned_to=setup_data["owner_id"],   # assigned to owner, not worker
        status=TaskStatus.pending,
    )
    db.add(task2)
    db.commit()
    db.refresh(task2)
    db.close()

    resp = client.get(
        f"/api/v1/worker/me/hkops/{biz}/tasks/{task2.id}",
        headers=auth(setup_data["worker_token"]),
    )
    assert resp.status_code == 403
