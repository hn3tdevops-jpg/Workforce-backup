"""
HKops API — Housekeeping Operations.

Routers exported:
  worker_router   GET/PATCH  /api/v1/worker/me/hkops/{business_id}     — worker sees & updates own tasks
  tenant_router   CRUD       /api/v1/tenant/{business_id}/hkops         — manager runs room board
  control_router  GET        /api/v1/control/hkops                      — superadmin analytics

Permissions:
  hkops:manage  — create/edit rooms, task types, assignments, inspections
  hkops:read    — read-only access to room board / tasks
"""
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.auth_deps import CurrentUser, _get_user_permissions
from app.core.db import get_db
from app.models.identity import AuditEvent, Membership, MembershipStatus
from app.models.hkops import (
    HKRoom, HKTaskType, HKTask, HKInspection,
    RoomStatus, TaskStatus, TaskPriority, InspectionResult,
)

# ── Router declarations ───────────────────────────────────────────────────────

worker_router  = APIRouter(prefix="/api/v1/worker/me/hkops/{business_id}", tags=["hkops"])
tenant_router  = APIRouter(prefix="/api/v1/tenant/{business_id}/hkops",    tags=["hkops"])
control_router = APIRouter(prefix="/api/v1/control/hkops",                 tags=["hkops"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_perm(user: CurrentUser, business_id: str, perm: str, db: Session) -> None:
    if user.is_superadmin:
        return
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and perm not in perms:
        raise HTTPException(403, f"Missing permission: {perm}")


def _require_membership(user_id: str, business_id: str, db: Session) -> Membership:
    m = db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "No active membership in this business")
    return m


def _audit(db: Session, actor_id: str, business_id: str, action: str, resource_id: str, detail: str = "") -> None:
    try:
        ev = AuditEvent(
            actor_id=actor_id,
            business_id=business_id,
            action=action,
            resource_type="hkops",
            resource_id=resource_id,
            detail=detail,
        )
        db.add(ev)
    except Exception:
        pass  # never let audit failure break the request


def _room_dict(r: HKRoom) -> dict:
    return {
        "id": r.id, "business_id": r.business_id, "location_id": r.location_id,
        "room_number": r.room_number, "floor": r.floor, "wing": r.wing,
        "room_type": r.room_type, "status": r.status, "notes": r.notes,
        "is_active": r.is_active, "created_at": r.created_at, "updated_at": r.updated_at,
    }


def _task_type_dict(t: HKTaskType) -> dict:
    return {
        "id": t.id, "business_id": t.business_id, "name": t.name,
        "description": t.description,
        "default_duration_minutes": t.default_duration_minutes,
        "requires_inspection": t.requires_inspection, "is_active": t.is_active,
        "created_at": t.created_at,
    }


def _task_dict(t: HKTask) -> dict:
    return {
        "id": t.id, "business_id": t.business_id, "room_id": t.room_id,
        "task_type_id": t.task_type_id, "assigned_to": t.assigned_to,
        "created_by": t.created_by, "status": t.status, "priority": t.priority,
        "scheduled_date": t.scheduled_date, "scheduled_start": t.scheduled_start,
        "scheduled_end": t.scheduled_end,
        "started_at": t.started_at, "completed_at": t.completed_at,
        "notes": t.notes, "supervisor_notes": t.supervisor_notes,
        "created_at": t.created_at, "updated_at": t.updated_at,
    }


def _inspection_dict(i: HKInspection) -> dict:
    return {
        "id": i.id, "task_id": i.task_id, "business_id": i.business_id,
        "inspector_id": i.inspector_id, "result": i.result, "score": i.score,
        "issues": i.issues_list, "notes": i.notes, "inspected_at": i.inspected_at,
        "created_at": i.created_at,
    }


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class RoomCreate(BaseModel):
    room_number: str
    floor: Optional[str] = None
    wing: Optional[str] = None
    room_type: Optional[str] = None
    location_id: Optional[str] = None
    notes: Optional[str] = None


class RoomUpdate(BaseModel):
    room_number: Optional[str] = None
    floor: Optional[str] = None
    wing: Optional[str] = None
    room_type: Optional[str] = None
    location_id: Optional[str] = None
    status: Optional[RoomStatus] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class TaskTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    default_duration_minutes: int = 30
    requires_inspection: bool = False


class TaskTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    default_duration_minutes: Optional[int] = None
    requires_inspection: Optional[bool] = None
    is_active: Optional[bool] = None


class TaskCreate(BaseModel):
    room_id: str
    task_type_id: str
    assigned_to: Optional[str] = None
    priority: TaskPriority = TaskPriority.normal
    scheduled_date: Optional[str] = None   # "2026-03-01"
    scheduled_start: Optional[str] = None  # "09:00"
    scheduled_end: Optional[str] = None    # "10:00"
    notes: Optional[str] = None


class TaskAssign(BaseModel):
    assigned_to: Optional[str] = None   # null to unassign
    priority: Optional[TaskPriority] = None
    scheduled_date: Optional[str] = None
    scheduled_start: Optional[str] = None
    scheduled_end: Optional[str] = None
    supervisor_notes: Optional[str] = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus
    notes: Optional[str] = None   # worker completion notes


class InspectionCreate(BaseModel):
    task_id: str
    result: InspectionResult
    score: Optional[int] = None    # 0–100
    issues: Optional[list[str]] = None
    notes: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════
# WORKER PLANE
# ════════════════════════════════════════════════════════════════════════════

@worker_router.get("/tasks", summary="My HK tasks for today")
def worker_my_tasks(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    scheduled_date: Optional[str] = Query(None, description="Filter by date YYYY-MM-DD"),
    status: Optional[TaskStatus] = Query(None),
):
    _require_membership(user.id, business_id, db)
    q = select(HKTask).where(
        HKTask.business_id == business_id,
        HKTask.assigned_to == user.id,
    )
    if scheduled_date:
        q = q.where(HKTask.scheduled_date == scheduled_date)
    if status:
        q = q.where(HKTask.status == status)
    tasks = db.execute(q.order_by(HKTask.priority.desc(), HKTask.scheduled_start)).scalars().all()
    return [_task_dict(t) for t in tasks]


@worker_router.patch("/tasks/{task_id}/status", summary="Update my task status")
def worker_update_task_status(
    business_id: str,
    task_id: str,
    body: TaskStatusUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_membership(user.id, business_id, db)
    task = db.get(HKTask, task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    if task.assigned_to != user.id and not user.is_superadmin:
        raise HTTPException(403, "Not assigned to this task")

    task.status = body.status
    if body.notes:
        task.notes = body.notes
    if body.status == TaskStatus.in_progress and not task.started_at:
        task.started_at = _now()
    if body.status == TaskStatus.completed:
        task.completed_at = _now()
        # Sync room status if task type doesn't require inspection
        room = db.get(HKRoom, task.room_id)
        tt = db.get(HKTaskType, task.task_type_id)
        if room and tt and not tt.requires_inspection:
            room.status = RoomStatus.clean

    _audit(db, user.id, business_id, f"hktask.{body.status}", task_id)
    db.commit()
    return _task_dict(task)


@worker_router.get("/tasks/{task_id}", summary="Get task detail")
def worker_get_task(
    business_id: str,
    task_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_membership(user.id, business_id, db)
    task = db.get(HKTask, task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    if task.assigned_to != user.id and not user.is_superadmin:
        raise HTTPException(403, "Not assigned to this task")
    return _task_dict(task)


# ════════════════════════════════════════════════════════════════════════════
# TENANT PLANE — Rooms
# ════════════════════════════════════════════════════════════════════════════

@tenant_router.post("/rooms", summary="Create room", status_code=201)
def create_room(
    business_id: str,
    body: RoomCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    room = HKRoom(
        business_id=business_id,
        location_id=body.location_id,
        room_number=body.room_number,
        floor=body.floor,
        wing=body.wing,
        room_type=body.room_type,
        notes=body.notes,
    )
    db.add(room)
    _audit(db, user.id, business_id, "hkroom.create", room.id, body.room_number)
    db.commit()
    db.refresh(room)
    return _room_dict(room)


@tenant_router.get("/rooms", summary="List rooms / room board")
def list_rooms(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    status: Optional[RoomStatus] = Query(None),
    location_id: Optional[str] = Query(None),
    floor: Optional[str] = Query(None),
    wing: Optional[str] = Query(None),
    active_only: bool = Query(True),
):
    _require_perm(user, business_id, "hkops:read", db)
    q = select(HKRoom).where(HKRoom.business_id == business_id)
    if status:
        q = q.where(HKRoom.status == status)
    if location_id:
        q = q.where(HKRoom.location_id == location_id)
    if floor:
        q = q.where(HKRoom.floor == floor)
    if wing:
        q = q.where(HKRoom.wing == wing)
    if active_only:
        q = q.where(HKRoom.is_active == True)  # noqa: E712
    rooms = db.execute(q.order_by(HKRoom.floor, HKRoom.room_number)).scalars().all()
    return [_room_dict(r) for r in rooms]


@tenant_router.get("/rooms/{room_id}", summary="Get room detail")
def get_room(
    business_id: str,
    room_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:read", db)
    room = db.get(HKRoom, room_id)
    if not room or room.business_id != business_id:
        raise HTTPException(404, "Room not found")
    return _room_dict(room)


@tenant_router.patch("/rooms/{room_id}", summary="Update room")
def update_room(
    business_id: str,
    room_id: str,
    body: RoomUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    room = db.get(HKRoom, room_id)
    if not room or room.business_id != business_id:
        raise HTTPException(404, "Room not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(room, field, val)
    _audit(db, user.id, business_id, "hkroom.update", room_id)
    db.commit()
    db.refresh(room)
    return _room_dict(room)


@tenant_router.delete("/rooms/{room_id}", summary="Deactivate room", status_code=204)
def deactivate_room(
    business_id: str,
    room_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    room = db.get(HKRoom, room_id)
    if not room or room.business_id != business_id:
        raise HTTPException(404, "Room not found")
    room.is_active = False
    _audit(db, user.id, business_id, "hkroom.deactivate", room_id)
    db.commit()


# ── Tenant — Task Types ───────────────────────────────────────────────────────

@tenant_router.post("/task-types", summary="Create task type", status_code=201)
def create_task_type(
    business_id: str,
    body: TaskTypeCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    tt = HKTaskType(
        business_id=business_id,
        name=body.name,
        description=body.description,
        default_duration_minutes=body.default_duration_minutes,
        requires_inspection=body.requires_inspection,
    )
    db.add(tt)
    _audit(db, user.id, business_id, "hktasktype.create", tt.id, body.name)
    db.commit()
    db.refresh(tt)
    return _task_type_dict(tt)


@tenant_router.get("/task-types", summary="List task types")
def list_task_types(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    active_only: bool = Query(True),
):
    _require_perm(user, business_id, "hkops:read", db)
    q = select(HKTaskType).where(HKTaskType.business_id == business_id)
    if active_only:
        q = q.where(HKTaskType.is_active == True)  # noqa: E712
    return [_task_type_dict(t) for t in db.execute(q).scalars().all()]


@tenant_router.patch("/task-types/{type_id}", summary="Update task type")
def update_task_type(
    business_id: str,
    type_id: str,
    body: TaskTypeUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    tt = db.get(HKTaskType, type_id)
    if not tt or tt.business_id != business_id:
        raise HTTPException(404, "Task type not found")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(tt, field, val)
    _audit(db, user.id, business_id, "hktasktype.update", type_id)
    db.commit()
    db.refresh(tt)
    return _task_type_dict(tt)


# ── Tenant — Tasks ────────────────────────────────────────────────────────────

@tenant_router.post("/tasks", summary="Create & assign task", status_code=201)
def create_task(
    business_id: str,
    body: TaskCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    # Validate room and task type belong to this business
    room = db.get(HKRoom, body.room_id)
    if not room or room.business_id != business_id:
        raise HTTPException(404, "Room not found")
    tt = db.get(HKTaskType, body.task_type_id)
    if not tt or tt.business_id != business_id:
        raise HTTPException(404, "Task type not found")

    task = HKTask(
        business_id=business_id,
        room_id=body.room_id,
        task_type_id=body.task_type_id,
        assigned_to=body.assigned_to,
        created_by=user.id,
        priority=body.priority,
        scheduled_date=body.scheduled_date,
        scheduled_start=body.scheduled_start,
        scheduled_end=body.scheduled_end,
        notes=body.notes,
    )
    db.add(task)
    # Mark room as dirty when a new task is created (unless already flagged OOO/DND)
    if room.status not in (RoomStatus.out_of_order, RoomStatus.do_not_disturb):
        room.status = RoomStatus.dirty

    _audit(db, user.id, business_id, "hktask.create", task.id,
           f"room={body.room_id} type={body.task_type_id}")
    db.commit()
    db.refresh(task)
    return _task_dict(task)


@tenant_router.get("/tasks", summary="List tasks")
def list_tasks(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    room_id: Optional[str] = Query(None),
    assigned_to: Optional[str] = Query(None),
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    scheduled_date: Optional[str] = Query(None),
):
    _require_perm(user, business_id, "hkops:read", db)
    q = select(HKTask).where(HKTask.business_id == business_id)
    if room_id:
        q = q.where(HKTask.room_id == room_id)
    if assigned_to:
        q = q.where(HKTask.assigned_to == assigned_to)
    if status:
        q = q.where(HKTask.status == status)
    if priority:
        q = q.where(HKTask.priority == priority)
    if scheduled_date:
        q = q.where(HKTask.scheduled_date == scheduled_date)
    tasks = db.execute(q.order_by(HKTask.priority.desc(), HKTask.scheduled_start)).scalars().all()
    return [_task_dict(t) for t in tasks]


@tenant_router.get("/tasks/{task_id}", summary="Get task detail")
def get_task(
    business_id: str,
    task_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:read", db)
    task = db.get(HKTask, task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    return _task_dict(task)


@tenant_router.patch("/tasks/{task_id}/assign", summary="Reassign / reschedule task")
def assign_task(
    business_id: str,
    task_id: str,
    body: TaskAssign,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    task = db.get(HKTask, task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    for field, val in body.model_dump(exclude_unset=True).items():
        setattr(task, field, val)
    _audit(db, user.id, business_id, "hktask.assign", task_id,
           f"assigned_to={body.assigned_to}")
    db.commit()
    db.refresh(task)
    return _task_dict(task)


@tenant_router.patch("/tasks/{task_id}/status", summary="Override task status")
def override_task_status(
    business_id: str,
    task_id: str,
    body: TaskStatusUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    task = db.get(HKTask, task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    task.status = body.status
    if body.notes:
        task.supervisor_notes = body.notes
    if body.status == TaskStatus.completed and not task.completed_at:
        task.completed_at = _now()
    _audit(db, user.id, business_id, f"hktask.override.{body.status}", task_id)
    db.commit()
    db.refresh(task)
    return _task_dict(task)


# ── Tenant — Inspections ──────────────────────────────────────────────────────

@tenant_router.post("/inspections", summary="Submit inspection result", status_code=201)
def create_inspection(
    business_id: str,
    body: InspectionCreate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:manage", db)
    task = db.get(HKTask, body.task_id)
    if not task or task.business_id != business_id:
        raise HTTPException(404, "Task not found")
    if task.status not in (TaskStatus.completed, TaskStatus.flagged):
        raise HTTPException(422, "Can only inspect completed or flagged tasks")
    if task.inspection:
        raise HTTPException(409, "Inspection already exists for this task")

    inspection = HKInspection(
        task_id=body.task_id,
        business_id=business_id,
        inspector_id=user.id,
        result=body.result,
        score=body.score,
        issues=json.dumps(body.issues or []),
        notes=body.notes,
    )
    db.add(inspection)

    # Update room status based on inspection result
    room = db.get(HKRoom, task.room_id)
    if room:
        if body.result == InspectionResult.pass_:
            room.status = RoomStatus.inspected
        elif body.result == InspectionResult.fail:
            room.status = RoomStatus.dirty   # needs re-clean
            task.status = TaskStatus.flagged
        # conditional → stays clean but noted

    _audit(db, user.id, business_id, f"hkinspection.{body.result}", body.task_id,
           f"score={body.score}")
    db.commit()
    db.refresh(inspection)
    return _inspection_dict(inspection)


@tenant_router.get("/inspections", summary="List inspections")
def list_inspections(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    room_id: Optional[str] = Query(None),
    result: Optional[InspectionResult] = Query(None),
    scheduled_date: Optional[str] = Query(None),
):
    _require_perm(user, business_id, "hkops:read", db)
    q = select(HKInspection).where(HKInspection.business_id == business_id)
    if result:
        q = q.where(HKInspection.result == result)
    # Filter by room via join
    if room_id:
        q = q.join(HKTask, HKInspection.task_id == HKTask.id).where(HKTask.room_id == room_id)
    inspections = db.execute(q.order_by(HKInspection.inspected_at.desc())).scalars().all()
    return [_inspection_dict(i) for i in inspections]


@tenant_router.get("/inspections/{inspection_id}", summary="Get inspection detail")
def get_inspection(
    business_id: str,
    inspection_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "hkops:read", db)
    insp = db.get(HKInspection, inspection_id)
    if not insp or insp.business_id != business_id:
        raise HTTPException(404, "Inspection not found")
    return _inspection_dict(insp)


# ── Tenant — Dashboard summary ────────────────────────────────────────────────

@tenant_router.get("/summary", summary="Room board summary counts")
def room_board_summary(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    scheduled_date: Optional[str] = Query(None),
):
    """Returns counts per room status and task status for a quick dashboard widget."""
    _require_perm(user, business_id, "hkops:read", db)

    room_counts = db.execute(
        select(HKRoom.status, func.count(HKRoom.id))
        .where(HKRoom.business_id == business_id, HKRoom.is_active == True)  # noqa: E712
        .group_by(HKRoom.status)
    ).all()

    task_q = select(HKTask.status, func.count(HKTask.id)).where(
        HKTask.business_id == business_id
    )
    if scheduled_date:
        task_q = task_q.where(HKTask.scheduled_date == scheduled_date)
    task_counts = db.execute(task_q.group_by(HKTask.status)).all()

    return {
        "rooms": {str(s): c for s, c in room_counts},
        "tasks": {str(s): c for s, c in task_counts},
    }


# ════════════════════════════════════════════════════════════════════════════
# CONTROL PLANE — superadmin analytics
# ════════════════════════════════════════════════════════════════════════════

@control_router.get("/stats", summary="Cross-tenant HKops stats")
def control_stats(
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if not user.is_superadmin:
        raise HTTPException(403, "Superadmin only")

    room_total = db.execute(
        select(func.count(HKRoom.id)).where(HKRoom.is_active == True)  # noqa: E712
    ).scalar()
    task_total = db.execute(select(func.count(HKTask.id))).scalar()
    inspection_total = db.execute(select(func.count(HKInspection.id))).scalar()

    room_by_status = db.execute(
        select(HKRoom.status, func.count(HKRoom.id))
        .where(HKRoom.is_active == True)  # noqa: E712
        .group_by(HKRoom.status)
    ).all()

    insp_by_result = db.execute(
        select(HKInspection.result, func.count(HKInspection.id))
        .group_by(HKInspection.result)
    ).all()

    return {
        "rooms_active": room_total,
        "tasks_total": task_total,
        "inspections_total": inspection_total,
        "rooms_by_status": {str(s): c for s, c in room_by_status},
        "inspections_by_result": {str(r): c for r, c in insp_by_result},
    }
