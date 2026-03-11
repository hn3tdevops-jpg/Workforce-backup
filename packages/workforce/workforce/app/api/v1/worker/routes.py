"""
Worker plane routes — self-scoped employee portal.
Workers can only see and modify their own data within their memberships.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, _get_user_permissions
from apps.api.app.core.db import get_db
from apps.api.app.models.identity import Membership, MembershipStatus, WorkerAvailability, WorkerProfile
from apps.api.app.models.business import Business
from apps.api.app.models.schedule import ScheduleAssignment, ScheduleShift

router = APIRouter(prefix="/api/v1/worker", tags=["worker"])


def _get_active_membership(
    user_id: str, business_id: str, db: Session, is_superadmin: bool = False
) -> Optional[Membership]:
    """Returns the user's active membership. Always performs a DB lookup —
    superadmins are treated like any other user for worker self-service endpoints."""
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


def _get_any_membership(
    user_id: str, business_id: str, db: Session, is_superadmin: bool = False
) -> Optional[Membership]:
    """Like _get_active_membership but accepts any non-removed membership status.
    Used for endpoints (e.g. availability) that don't require active status.
    Unlike _get_active_membership, does NOT bypass lookup for superadmins —
    availability records are tied to an actual membership row."""
    m = db.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.business_id == business_id,
            Membership.status != MembershipStatus.removed,
        )
    ).scalar_one_or_none()
    if not m:
        raise HTTPException(403, "No membership in this business")
    return m


# ── My Profile ────────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None


class WorkerProfileUpdate(BaseModel):
    job_title: Optional[str] = None
    pay_rate: Optional[float] = None
    hire_date: Optional[str] = None
    notes: Optional[str] = None
    qualified_roles: Optional[list] = None
    skills: Optional[list] = None
    certifications: Optional[list] = None
    max_weekly_hours: Optional[int] = None


@router.get("/me/profile")
def get_my_profile(user: CurrentUser, db: Session = Depends(get_db)):
    return {
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "bio": user.bio,
        "emergency_contact_name": user.emergency_contact_name,
        "emergency_contact_phone": user.emergency_contact_phone,
        "is_superadmin": user.is_superadmin,
        "status": user.status,
        "created_at": str(user.created_at) if user.created_at else None,
    }


@router.patch("/me/profile")
def update_my_profile(payload: ProfileUpdate, user: CurrentUser, db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return get_my_profile(user, db)


@router.get("/me/profile/{business_id}")
def get_my_worker_profile(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    import json as _json
    m = _get_active_membership(user.id, business_id, db, user.is_superadmin)
    mid = m.id if m else None
    wp = db.execute(select(WorkerProfile).where(WorkerProfile.membership_id == mid)).scalar_one_or_none() if mid else None
    def _jl(v):
        try:
            return _json.loads(v) if v else []
        except Exception:
            return []
    return {
        "membership_id": mid,
        "job_title": wp.job_title if wp else None,
        "pay_rate": wp.pay_rate if wp else None,
        "hire_date": wp.hire_date if wp else None,
        "notes": wp.notes if wp else None,
        "qualified_roles": _jl(wp.qualified_roles) if wp else [],
        "skills": _jl(wp.skills) if wp else [],
        "certifications": _jl(wp.certifications) if wp else [],
        "max_weekly_hours": wp.max_weekly_hours if wp else None,
    }


@router.patch("/me/profile/{business_id}")
def update_my_worker_profile(
    business_id: str,
    payload: WorkerProfileUpdate,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    import json as _json
    m = _get_active_membership(user.id, business_id, db, user.is_superadmin)
    mid = m.id if m else None
    wp = db.execute(select(WorkerProfile).where(WorkerProfile.membership_id == mid)).scalar_one_or_none() if mid else None
    if not wp and mid:
        wp = WorkerProfile(membership_id=mid)
        db.add(wp)
    updates = payload.model_dump(exclude_none=True)
    # Workers can update their own qualifications/skills as self-declaration
    json_fields = {"qualified_roles", "skills", "certifications"}
    allowed = {"job_title", "hire_date", "qualified_roles", "skills", "certifications", "max_weekly_hours"}
    if wp:
        for field, value in updates.items():
            if field in allowed:
                setattr(wp, field, _json.dumps(value) if field in json_fields else value)
        db.commit()
        db.refresh(wp)
    return get_my_worker_profile(business_id, user, db)




# ── My memberships ────────────────────────────────────────────────────────────

@router.get("/me/permissions/{business_id}")
def my_permissions(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    """Return the set of permission keys the current user has in a business."""
    perms = _get_user_permissions(user, business_id, db)
    return {"business_id": business_id, "permissions": sorted(perms)}


@router.get("/me/memberships")
def my_memberships(user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.execute(
        select(Membership, Business)
        .join(Business, Business.id == Membership.business_id)
        .where(
            Membership.user_id == user.id,
            Membership.status != MembershipStatus.removed,
            Business.deleted_at == None,  # noqa: E711
        )
    ).all()
    return [
        {"business_id": m.business_id, "business_name": b.name, "status": m.status, "primary_location_id": m.primary_location_id}
        for m, b in rows
    ]


# ── Schedule ──────────────────────────────────────────────────────────────────

@router.get("/me/schedule/{business_id}")
def my_schedule(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    membership = _get_active_membership(user.id, business_id, db, user.is_superadmin)
    if not membership:
        return []
    rows = db.execute(
        select(ScheduleAssignment, ScheduleShift)
        .join(ScheduleShift, ScheduleShift.id == ScheduleAssignment.shift_id)
        .where(ScheduleAssignment.membership_id == membership.id)
        .order_by(ScheduleShift.start_ts)
    ).all()
    def _ts(dt):
        if not dt:
            return None
        s = dt.isoformat() if hasattr(dt, "isoformat") else str(dt)
        return s if s.endswith('Z') or '+' in s else s + 'Z'
    return [
        {
            "shift_id": shift.id,
            "title": shift.title,
            "role_name": shift.role_name,
            "location_id": shift.location_id,
            "start_ts": _ts(shift.start_ts),
            "end_ts": _ts(shift.end_ts),
            "status": assignment.status,
            "shift_status": shift.status,
            "color": shift.color,
        }
        for assignment, shift in rows
    ]


# ── Availability ──────────────────────────────────────────────────────────────

class AvailabilityRequest(BaseModel):
    day_of_week: int  # 0=Mon … 6=Sun
    start_hour: float
    end_hour: float


@router.get("/me/availability/{business_id}")
def my_availability(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    membership = _get_any_membership(user.id, business_id, db, user.is_superadmin)
    if not membership:
        return []
    rows = db.execute(
        select(WorkerAvailability).where(WorkerAvailability.membership_id == membership.id)
        .order_by(WorkerAvailability.day_of_week, WorkerAvailability.start_hour)
    ).scalars().all()
    return [
        {
            "id": a.id,
            "day_of_week": a.day_of_week,
            "start_hour": a.start_hour,
            "end_hour": a.end_hour,
        }
        for a in rows
    ]


@router.post("/me/availability/{business_id}", status_code=201)
def set_availability(
    business_id: str,
    payload: AvailabilityRequest,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    membership = _get_any_membership(user.id, business_id, db, user.is_superadmin)
    if not membership:
        raise HTTPException(403, "No membership in this business")
    block = WorkerAvailability(
        membership_id=membership.id,
        day_of_week=payload.day_of_week,
        start_hour=payload.start_hour,
        end_hour=payload.end_hour,
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return {"id": block.id, "day_of_week": block.day_of_week, "start_hour": block.start_hour, "end_hour": block.end_hour}


@router.delete("/me/availability/{business_id}/{block_id}", status_code=204)
def delete_availability(
    business_id: str,
    block_id: str,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    membership = _get_any_membership(user.id, business_id, db, user.is_superadmin)
    if not membership:
        raise HTTPException(403, "No membership in this business")
    block = db.execute(
        select(WorkerAvailability).where(
            WorkerAvailability.id == block_id,
            WorkerAvailability.membership_id == membership.id,
        )
    ).scalar_one_or_none()
    if not block:
        raise HTTPException(404, "Availability block not found")
    db.delete(block)
    db.commit()
