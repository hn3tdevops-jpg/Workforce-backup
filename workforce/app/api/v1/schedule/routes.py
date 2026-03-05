"""
Schedule API — tenant-scoped shift management.
Provides CRUD for ScheduleShift + assignments, plus a week-view calendar endpoint,
list/filter endpoint, and bulk-assign endpoint.
"""
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import CurrentUser, require_permission
from app.core.db import get_db
from app.models.business import Location
from app.models.identity import Membership, User
from app.models.schedule import AssignmentStatus, ScheduleAssignment, ScheduleShift, ShiftStatus

router = APIRouter(prefix="/api/v1/tenant/{business_id}/schedule", tags=["schedule"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_ts(dt) -> str | None:
    """Serialize a datetime to ISO 8601 UTC string with Z suffix."""
    if dt is None:
        return None
    s = dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
    # Ensure Z suffix so browsers parse as UTC (SQLite drops tzinfo)
    if s and not s.endswith('Z') and '+' not in s and s != 'None':
        s += 'Z'
    return s


def _shift_out(shift: ScheduleShift, db: Session) -> dict:
    """Serialize a shift with its assignment/member info."""
    assignments = []
    for a in shift.assignments:
        m = db.get(Membership, a.membership_id)
        if m:
            u = db.get(User, m.user_id)
            assignments.append({
                "id": a.id,
                "membership_id": a.membership_id,
                "status": a.status,
                "email": u.email if u else None,
                "name": _display_name(u) if u else None,
            })
    loc_name = None
    if shift.location_id:
        loc = db.get(Location, shift.location_id)
        loc_name = loc.name if loc else None
    return {
        "id": shift.id,
        "business_id": shift.business_id,
        "title": shift.title,
        "role_name": shift.role_name,
        "location_id": shift.location_id,
        "location_name": loc_name,
        "start_ts": _fmt_ts(shift.start_ts),
        "end_ts": _fmt_ts(shift.end_ts),
        "needed_count": shift.needed_count,
        "status": shift.status,
        "color": shift.color,
        "notes": shift.notes,
        "assignments": assignments,
        "assigned_count": len(assignments),
        "created_at": _fmt_ts(shift.created_at),
    }


def _display_name(u: User | None) -> str:
    if not u:
        return "Unknown"
    if u.first_name or u.last_name:
        return " ".join(filter(None, [u.first_name, u.last_name]))
    return u.email.split("@")[0]


def _parse_dt(s: str) -> datetime:
    """Parse ISO datetime string, handling various formats."""
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        raise HTTPException(400, f"Invalid datetime: {s!r}")


# ── Week calendar view ────────────────────────────────────────────────────────

@router.get("", dependencies=[require_permission("schedule:read")])
def get_schedule(
    business_id: str,
    week: str,  # ISO date of the Monday: e.g. 2026-02-17
    location_id: Optional[str] = None,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    """Return all shifts for the 7-day week starting on `week` date."""
    try:
        week_start = datetime.fromisoformat(week).replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
    except Exception:
        raise HTTPException(400, "week must be ISO date YYYY-MM-DD")
    week_end = week_start + timedelta(days=7)

    conditions = [
        ScheduleShift.business_id == business_id,
        ScheduleShift.start_ts >= week_start,
        ScheduleShift.start_ts < week_end,
    ]
    if location_id:
        conditions.append(ScheduleShift.location_id == location_id)

    shifts = db.execute(
        select(ScheduleShift).where(*conditions).order_by(ScheduleShift.start_ts)
    ).scalars().all()

    return [_shift_out(s, db) for s in shifts]


# ── CRUD ──────────────────────────────────────────────────────────────────────

class ShiftCreate(BaseModel):
    title: str
    start_ts: str
    end_ts: str
    role_name: Optional[str] = None
    location_id: Optional[str] = None
    needed_count: int = 1
    status: str = "draft"
    color: Optional[str] = None
    notes: Optional[str] = None


class ShiftUpdate(BaseModel):
    title: Optional[str] = None
    start_ts: Optional[str] = None
    end_ts: Optional[str] = None
    role_name: Optional[str] = None
    location_id: Optional[str] = None
    needed_count: Optional[int] = None
    status: Optional[str] = None
    color: Optional[str] = None
    notes: Optional[str] = None


@router.post("/shifts", status_code=201, dependencies=[require_permission("schedule:write")])
def create_shift(
    business_id: str,
    payload: ShiftCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    try:
        status = ShiftStatus(payload.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status: {payload.status}")

    shift = ScheduleShift(
        business_id=business_id,
        title=payload.title,
        role_name=payload.role_name,
        location_id=payload.location_id,
        start_ts=_parse_dt(payload.start_ts),
        end_ts=_parse_dt(payload.end_ts),
        needed_count=payload.needed_count,
        status=status,
        color=payload.color,
        notes=payload.notes,
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return _shift_out(shift, db)


@router.get("/shifts/{shift_id}", dependencies=[require_permission("schedule:read")])
def get_shift(
    business_id: str,
    shift_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    shift = db.get(ScheduleShift, shift_id)
    if not shift or shift.business_id != business_id:
        raise HTTPException(404, "Shift not found")
    return _shift_out(shift, db)


@router.patch("/shifts/{shift_id}", dependencies=[require_permission("schedule:write")])
def update_shift(
    business_id: str,
    shift_id: str,
    payload: ShiftUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    shift = db.get(ScheduleShift, shift_id)
    if not shift or shift.business_id != business_id:
        raise HTTPException(404, "Shift not found")
    updates = payload.model_dump(exclude_none=True)
    for field, value in updates.items():
        if field in ("start_ts", "end_ts"):
            setattr(shift, field, _parse_dt(value))
        elif field == "status":
            try:
                setattr(shift, field, ShiftStatus(value))
            except ValueError:
                raise HTTPException(400, f"Invalid status: {value}")
        else:
            setattr(shift, field, value)
    db.commit()
    db.refresh(shift)
    return _shift_out(shift, db)


@router.delete("/shifts/{shift_id}", status_code=204, dependencies=[require_permission("schedule:write")])
def delete_shift(
    business_id: str,
    shift_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    shift = db.get(ScheduleShift, shift_id)
    if not shift or shift.business_id != business_id:
        raise HTTPException(404, "Shift not found")
    db.delete(shift)
    db.commit()


# ── Assignments ───────────────────────────────────────────────────────────────

class AssignmentCreate(BaseModel):
    membership_id: str
    status: str = "assigned"


# ── List / filter shifts (audit view) ────────────────────────────────────────

@router.get("/shifts", dependencies=[require_permission("schedule:read")])
def list_shifts(
    business_id: str,
    date_from: Optional[str] = Query(None, description="ISO date YYYY-MM-DD, inclusive"),
    date_to: Optional[str] = Query(None, description="ISO date YYYY-MM-DD, inclusive"),
    status: Optional[str] = Query(None),
    role_name: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    membership_id: Optional[str] = Query(None, description="Filter to shifts assigned to this member"),
    limit: int = Query(500, le=1000),
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    """Return shifts matching the given filters — used by the audit/list view."""
    conditions = [ScheduleShift.business_id == business_id]

    if date_from:
        try:
            dt = datetime.fromisoformat(date_from).replace(hour=0, minute=0, second=0, tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(400, "date_from must be YYYY-MM-DD")
        conditions.append(ScheduleShift.start_ts >= dt)

    if date_to:
        try:
            dt = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(400, "date_to must be YYYY-MM-DD")
        conditions.append(ScheduleShift.start_ts <= dt)

    if status:
        try:
            conditions.append(ScheduleShift.status == ShiftStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")

    if role_name:
        conditions.append(ScheduleShift.role_name.ilike(f"%{role_name}%"))

    if location_id:
        conditions.append(ScheduleShift.location_id == location_id)

    q = select(ScheduleShift).where(*conditions).order_by(ScheduleShift.start_ts).limit(limit)

    if membership_id:
        # Filter to shifts that have this member assigned
        assigned_shift_ids = db.execute(
            select(ScheduleAssignment.shift_id).where(
                ScheduleAssignment.membership_id == membership_id
            )
        ).scalars().all()
        q = select(ScheduleShift).where(
            *conditions, ScheduleShift.id.in_(assigned_shift_ids)
        ).order_by(ScheduleShift.start_ts).limit(limit)

    shifts = db.execute(q).scalars().all()
    return [_shift_out(s, db) for s in shifts]


# ── Bulk assign ────────────────────────────────────────────────────────────────

class BulkAssignPayload(BaseModel):
    shift_ids: List[str]
    membership_id: str


@router.post("/shifts/bulk-assign", dependencies=[require_permission("schedule:write")])
def bulk_assign(
    business_id: str,
    payload: BulkAssignPayload,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    """Assign a member to multiple shifts at once. Skips already-assigned shifts."""
    if not payload.shift_ids:
        raise HTTPException(400, "shift_ids must not be empty")

    m = db.get(Membership, payload.membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found in this business")

    u = db.get(User, m.user_id)

    assigned = []
    skipped = []
    for sid in payload.shift_ids:
        shift = db.get(ScheduleShift, sid)
        if not shift or shift.business_id != business_id:
            skipped.append({"shift_id": sid, "reason": "not found"})
            continue
        existing = db.execute(
            select(ScheduleAssignment).where(
                ScheduleAssignment.shift_id == sid,
                ScheduleAssignment.membership_id == payload.membership_id,
            )
        ).scalar_one_or_none()
        if existing:
            skipped.append({"shift_id": sid, "reason": "already assigned"})
            continue
        a = ScheduleAssignment(
            shift_id=sid,
            membership_id=payload.membership_id,
            status=AssignmentStatus.assigned,
        )
        db.add(a)
        assigned.append(sid)

    db.commit()
    return {
        "assigned_count": len(assigned),
        "skipped_count": len(skipped),
        "assigned_shift_ids": assigned,
        "skipped": skipped,
        "membership_id": payload.membership_id,
        "email": u.email if u else None,
        "name": _display_name(u) if u else None,
    }


@router.post("/shifts/{shift_id}/assignments", status_code=201, dependencies=[require_permission("schedule:write")])
def assign_member(
    business_id: str,
    shift_id: str,
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    shift = db.get(ScheduleShift, shift_id)
    if not shift or shift.business_id != business_id:
        raise HTTPException(404, "Shift not found")
    # Verify membership belongs to this business
    m = db.get(Membership, payload.membership_id)
    if not m or m.business_id != business_id:
        raise HTTPException(404, "Membership not found in this business")
    # Check not already assigned
    existing = db.execute(
        select(ScheduleAssignment).where(
            ScheduleAssignment.shift_id == shift_id,
            ScheduleAssignment.membership_id == payload.membership_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "Already assigned")
    try:
        status = AssignmentStatus(payload.status)
    except ValueError:
        status = AssignmentStatus.assigned
    a = ScheduleAssignment(
        shift_id=shift_id,
        membership_id=payload.membership_id,
        status=status,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    u = db.get(User, m.user_id)
    return {
        "id": a.id,
        "shift_id": shift_id,
        "membership_id": a.membership_id,
        "status": a.status,
        "email": u.email if u else None,
        "name": _display_name(u),
    }


@router.delete("/shifts/{shift_id}/assignments/{assignment_id}", status_code=204,
               dependencies=[require_permission("schedule:write")])
def remove_assignment(
    business_id: str,
    shift_id: str,
    assignment_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = None,
):
    a = db.get(ScheduleAssignment, assignment_id)
    if not a or a.shift_id != shift_id:
        raise HTTPException(404, "Assignment not found")
    db.delete(a)
    db.commit()
