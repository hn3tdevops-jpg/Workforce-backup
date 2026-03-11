"""
Timeclock routes split across worker and tenant planes.
Imported and registered in each plane's routes.py.
"""
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, _get_user_permissions
from apps.api.app.core.db import get_db
from apps.api.app.models.identity import AuditEvent, Membership, MembershipStatus, User
from apps.api.app.models.timeclock import TimeEntry, TimeEntryStatus

worker_router = APIRouter(prefix="/api/v1/worker/me/timeclock", tags=["timeclock"])
tenant_router = APIRouter(prefix="/api/v1/tenant/{business_id}/timeclock", tags=["timeclock"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_membership(user_id: str, business_id: str, db: Session, is_superadmin: bool = False) -> None:
    if is_superadmin:
        return
    m = db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "No active membership in this business")


def _entry_dict(e: TimeEntry) -> dict:
    cin = e.clocked_in_at
    if isinstance(cin, str):
        cin = datetime.fromisoformat(cin)
    if cin and cin.tzinfo is None:
        cin = cin.replace(tzinfo=timezone.utc)

    if e.clocked_out_at:
        cout = e.clocked_out_at
        if isinstance(cout, str):
            cout = datetime.fromisoformat(cout)
        if cout.tzinfo is None:
            cout = cout.replace(tzinfo=timezone.utc)
        live_minutes = e.total_minutes
    else:
        live_minutes = round((_now() - cin).total_seconds() / 60, 2) if cin else None

    return {
        "id": e.id,
        "user_id": e.user_id,
        "business_id": e.business_id,
        "location_id": e.location_id,
        "clocked_in_at": e.clocked_in_at,
        "clocked_out_at": e.clocked_out_at,
        "total_minutes": live_minutes,
        "notes": e.notes,
        "status": e.status,
    }


# ── Worker: clock in ──────────────────────────────────────────────────────────

class ClockInRequest(BaseModel):
    location_id: str | None = None
    notes: str | None = None


@worker_router.post("/{business_id}/clock-in", status_code=201)
def clock_in(business_id: str, payload: ClockInRequest, user: CurrentUser, db: Session = Depends(get_db)):
    _require_membership(user.id, business_id, db, user.is_superadmin)
    active = db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == user.id,
            TimeEntry.status == TimeEntryStatus.active,
        )
    ).scalar_one_or_none()
    if active:
        if active.business_id == business_id:
            raise HTTPException(409, "Already clocked in — clock out first")
        raise HTTPException(409, "Already clocked in at another location — clock out first")

    entry = TimeEntry(
        user_id=user.id, business_id=business_id,
        location_id=payload.location_id, notes=payload.notes,
        clocked_in_at=_now(), status=TimeEntryStatus.active,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _entry_dict(entry)


# ── Worker: clock out ─────────────────────────────────────────────────────────

class ClockOutRequest(BaseModel):
    notes: str | None = None


@worker_router.post("/{business_id}/clock-out")
def clock_out(business_id: str, payload: ClockOutRequest, user: CurrentUser, db: Session = Depends(get_db)):
    entry = db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == user.id,
            TimeEntry.business_id == business_id,
            TimeEntry.status == TimeEntryStatus.active,
        )
    ).scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "No active clock-in found")

    now = _now()
    cin = entry.clocked_in_at
    if isinstance(cin, str):
        cin = datetime.fromisoformat(cin)
    if cin.tzinfo is None:
        cin = cin.replace(tzinfo=timezone.utc)

    entry.clocked_out_at = now
    entry.total_minutes = round((now - cin).total_seconds() / 60, 2)
    entry.status = TimeEntryStatus.completed
    if payload.notes:
        entry.notes = payload.notes
    db.commit()
    db.refresh(entry)
    return _entry_dict(entry)


# ── Worker: status (are we clocked in?) ──────────────────────────────────────

@worker_router.get("/{business_id}/status")
def my_clock_status(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    membership = db.execute(
        select(Membership).where(
            Membership.user_id == user.id,
            Membership.business_id == business_id,
        )
    ).scalar_one_or_none()
    membership_status = membership.status if membership else None
    if membership_status != MembershipStatus.active:
        return {
            "clocked_in": False,
            "entry": None,
            "membership_status": membership_status,
            "can_clock_in": False,
        }
    entry = db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == user.id,
            TimeEntry.business_id == business_id,
            TimeEntry.status == TimeEntryStatus.active,
        )
    ).scalar_one_or_none()
    return {
        "clocked_in": entry is not None,
        "entry": _entry_dict(entry) if entry else None,
        "membership_status": membership_status,
        "can_clock_in": True,
    }


# ── Worker: my entries ────────────────────────────────────────────────────────

@worker_router.get("/{business_id}/entries")
def my_entries(business_id: str, user: CurrentUser, db: Session = Depends(get_db), limit: int = 30):
    _require_membership(user.id, business_id, db, user.is_superadmin)
    rows = db.execute(
        select(TimeEntry)
        .where(TimeEntry.user_id == user.id, TimeEntry.business_id == business_id)
        .order_by(TimeEntry.clocked_in_at.desc()).limit(limit)
    ).scalars().all()
    return [_entry_dict(e) for e in rows]


# ── Tenant: live clock-in status ─────────────────────────────────────────────

@tenant_router.get("/live")
def live_status(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    """
    Returns two lists:
      clocked_in  — employees currently active (green)
      expected    — employees with a shift approved for right now who are NOT clocked in (red)
    Each item includes user_id, email, and relevant timing.
    """
    if not user.is_superadmin:
        from apps.api.app.core.auth_deps import _get_user_permissions
        perms = _get_user_permissions(user, business_id, db)
        if "*" not in perms and "timeclock:manage" not in perms:
            raise HTTPException(403, "Missing permission: timeclock:manage")

    from apps.api.app.models.identity import User as UserModel
    from apps.api.app.models.marketplace import ShiftRequest, JobPosting, RequestStatus

    now = _now()
    today_str = now.strftime("%Y-%m-%d")
    now_time  = now.strftime("%H:%M")

    # --- clocked in right now ---
    active_entries = db.execute(
        select(TimeEntry).where(
            TimeEntry.business_id == business_id,
            TimeEntry.status == TimeEntryStatus.active,
        )
    ).scalars().all()

    clocked_in_user_ids = {e.user_id for e in active_entries}

    # resolve emails for clocked-in users
    user_emails: dict[str, str] = {}
    all_relevant_ids = set(clocked_in_user_ids)

    # --- expected: approved shift requests for today, shift window contains now ---
    expected_entries = []
    try:
        approved_reqs = db.execute(
            select(ShiftRequest, JobPosting)
            .join(JobPosting, ShiftRequest.posting_id == JobPosting.id)
            .where(
                ShiftRequest.business_id == business_id,
                ShiftRequest.status == RequestStatus.approved,
                JobPosting.shift_date == today_str,
            )
        ).all()

        for req, posting in approved_reqs:
            # Check if current time is within shift window
            if posting.shift_start and posting.shift_end:
                if not (posting.shift_start <= now_time <= posting.shift_end):
                    continue
            # Only flag as missing if not already clocked in
            if req.worker_id not in clocked_in_user_ids:
                all_relevant_ids.add(req.worker_id)
                expected_entries.append({
                    "user_id": req.worker_id,
                    "shift_start": posting.shift_start,
                    "shift_end": posting.shift_end,
                    "role_name": posting.role_name,
                    "title": posting.title,
                })
    except Exception:
        pass  # marketplace tables may not exist in all deployments

    # Batch-load emails
    if all_relevant_ids:
        users = db.execute(
            select(UserModel).where(UserModel.id.in_(all_relevant_ids))
        ).scalars().all()
        user_emails = {u.id: u.email for u in users}

    # Build clocked_in list with elapsed time
    clocked_in = []
    for e in active_entries:
        cin = e.clocked_in_at
        if isinstance(cin, str):
            from datetime import datetime as _dt
            cin = _dt.fromisoformat(cin)
        if cin.tzinfo is None:
            cin = cin.replace(tzinfo=timezone.utc)
        elapsed_mins = round((now - cin).total_seconds() / 60, 1)
        clocked_in.append({
            "user_id": e.user_id,
            "email": user_emails.get(e.user_id, e.user_id),
            "clocked_in_at": e.clocked_in_at,
            "elapsed_minutes": elapsed_mins,
            "location_id": e.location_id,
            "notes": e.notes,
        })

    # Attach emails to expected list
    for item in expected_entries:
        item["email"] = user_emails.get(item["user_id"], item["user_id"])

    return {
        "clocked_in": sorted(clocked_in, key=lambda x: x["email"]),
        "expected": sorted(expected_entries, key=lambda x: x["email"]),
        "as_of": now.isoformat(),
    }



@tenant_router.get("")
def list_all_entries(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
    limit: int = 100, status: str | None = None,
):
    if not user.is_superadmin:
        from apps.api.app.core.auth_deps import _get_user_permissions
        perms = _get_user_permissions(user, business_id, db)
        if "*" not in perms and "timeclock:manage" not in perms:
            raise HTTPException(403, "Missing permission: timeclock:manage")

    q = select(TimeEntry).where(TimeEntry.business_id == business_id)
    if status:
        try:
            q = q.where(TimeEntry.status == TimeEntryStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    rows = db.execute(q.order_by(TimeEntry.clocked_in_at.desc()).limit(limit)).scalars().all()
    return [_entry_dict(e) for e in rows]


# ── Tenant: approve / dispute ─────────────────────────────────────────────────

class ReviewRequest(BaseModel):
    status: str
    notes: str | None = None


@tenant_router.patch("/{entry_id}")
def review_entry(
    business_id: str, entry_id: str, payload: ReviewRequest,
    user: CurrentUser, db: Session = Depends(get_db),
):
    """Admin correction: update status/notes on a time entry and write an AuditEvent."""
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and "timeclock:manage" not in perms:
        raise HTTPException(403, "Missing permission: timeclock:manage")

    entry = db.get(TimeEntry, entry_id)
    if not entry or entry.business_id != business_id:
        raise HTTPException(404, "Entry not found")
    if entry.status == TimeEntryStatus.active:
        raise HTTPException(400, "Cannot review an active entry")

    before_status = entry.status.value
    try:
        entry.status = TimeEntryStatus(payload.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status '{payload.status}'. Use: approved, disputed, completed")
    if payload.notes:
        entry.notes = payload.notes

    # Write explicit audit event for admin corrections
    import json as _json
    from datetime import datetime as _dt
    audit = AuditEvent(
        business_id=business_id,
        actor_type="user",
        actor_id=user.id,
        action="timeclock.entry.corrected",
        entity="time_entry",
        entity_id=entry_id,
        diff_json=_json.dumps({
            "before_status": before_status,
            "after_status": payload.status,
            "notes": payload.notes,
        }),
        created_at=_dt.now(__import__("datetime").timezone.utc),
    )
    db.add(audit)
    db.commit()
    db.refresh(entry)
    return _entry_dict(entry)


# ── Tenant: summary (hours per user) ─────────────────────────────────────────

@tenant_router.get("/summary")
def timesheet_summary(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and "timeclock:manage" not in perms:
        raise HTTPException(403, "Missing permission: timeclock:manage")

    rows = db.execute(
        select(TimeEntry).where(
            TimeEntry.business_id == business_id,
            TimeEntry.status.in_([TimeEntryStatus.completed, TimeEntryStatus.approved]),
        )
    ).scalars().all()

    totals: dict[str, float] = {}
    for e in rows:
        totals[e.user_id] = round(totals.get(e.user_id, 0) + (e.total_minutes or 0), 2)

    return [
        {"user_id": uid, "total_minutes": mins, "total_hours": round(mins / 60, 2)}
        for uid, mins in sorted(totals.items(), key=lambda x: -x[1])
    ]


# ── Tenant: timecards (date-range rollup with by-day breakdown) ───────────────

@tenant_router.get("/timecards")
def timecards(
    business_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
    start: date = Query(..., description="Start date inclusive (YYYY-MM-DD)"),
    end: date = Query(..., description="End date inclusive (YYYY-MM-DD)"),
    user_id: str | None = Query(None, description="Filter to a specific user"),
):
    """
    Roll up completed/approved time entries by employee for a date range.
    Returns total_seconds, total_minutes, total_hours, and a by_day list.
    """
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and "timeclock:manage" not in perms:
        raise HTTPException(403, "Missing permission: timeclock:manage")

    start_dt = datetime(start.year, start.month, start.day, tzinfo=timezone.utc)
    end_dt = datetime(end.year, end.month, end.day, 23, 59, 59, tzinfo=timezone.utc)

    q = select(TimeEntry).where(
        TimeEntry.business_id == business_id,
        TimeEntry.status.in_([TimeEntryStatus.completed, TimeEntryStatus.approved]),
        TimeEntry.clocked_in_at >= start_dt,
        TimeEntry.clocked_in_at <= end_dt,
    )
    if user_id:
        q = q.where(TimeEntry.user_id == user_id)

    rows = db.execute(q.order_by(TimeEntry.clocked_in_at)).scalars().all()

    # Resolve user emails for display
    uids = {e.user_id for e in rows}
    email_map: dict[str, str] = {}
    if uids:
        users_list = db.execute(select(User).where(User.id.in_(uids))).scalars().all()
        email_map = {u.id: u.email for u in users_list}

    # Group by user_id then by day
    from collections import defaultdict
    by_user: dict[str, dict] = defaultdict(lambda: {"total_seconds": 0.0, "by_day": defaultdict(float)})

    for e in rows:
        mins = e.total_minutes or 0.0
        secs = mins * 60.0
        cin = e.clocked_in_at
        if isinstance(cin, str):
            cin = datetime.fromisoformat(cin)
        if cin and cin.tzinfo is None:
            cin = cin.replace(tzinfo=timezone.utc)
        day_key = cin.strftime("%Y-%m-%d") if cin else "unknown"
        by_user[e.user_id]["total_seconds"] += secs
        by_user[e.user_id]["by_day"][day_key] += secs

    result = []
    for uid, data in sorted(by_user.items()):
        total_secs = round(data["total_seconds"], 2)
        result.append({
            "user_id": uid,
            "email": email_map.get(uid, uid),
            "total_seconds": total_secs,
            "total_minutes": round(total_secs / 60, 2),
            "total_hours": round(total_secs / 3600, 2),
            "by_day": [
                {"date": d, "seconds": round(s, 2), "hours": round(s / 3600, 2)}
                for d, s in sorted(data["by_day"].items())
            ],
        })
    return {"start": str(start), "end": str(end), "timecards": result}


# ── Tenant: timeclock status for a specific user (service-to-service) ──────────

@tenant_router.get("/status/{target_user_id}")
def timeclock_status_for_user(
    business_id: str,
    target_user_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Returns the timeclock status for any user in the business.
    Used by service-to-service integrations (e.g., housekeeping).
    Requires timeclock:manage or superadmin.
    """
    perms = _get_user_permissions(user, business_id, db)
    if "*" not in perms and "timeclock:manage" not in perms:
        raise HTTPException(403, "Missing permission: timeclock:manage")

    entry = db.execute(
        select(TimeEntry).where(
            TimeEntry.user_id == target_user_id,
            TimeEntry.business_id == business_id,
            TimeEntry.status == TimeEntryStatus.active,
        )
    ).scalar_one_or_none()
    return {
        "user_id": target_user_id,
        "business_id": business_id,
        "clocked_in": entry is not None,
        "entry": _entry_dict(entry) if entry else None,
    }
