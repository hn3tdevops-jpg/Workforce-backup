"""
Shift Marketplace API — all planes combined in one file.

Routers exported:
  public_router    — GET /api/v1/marketplace/postings (searchable job board)
  worker_router    — worker shift/training/swap request actions
  tenant_router    — owner/manager post jobs, approve requests, manage swap rules
"""
from datetime import datetime, time, timezone
from typing import Optional
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from apps.api.app.core.auth_deps import CurrentUser, _get_user_permissions
from apps.api.app.core.db import get_db
from apps.api.app.models.identity import Membership, MembershipStatus, WorkerProfile, WorkerAvailability
from apps.api.app.models.marketplace import (
    JobPosting, PostingStatus,
    ShiftRequest, RequestStatus,
    TrainingRequest,
    ShiftSwapRequest, SwapStatus,
    SwapPermissionRule, SwapRuleEffect,
)
from apps.api.app.models.schedule import ScheduleAssignment, ScheduleShift

# ─── helpers ──────────────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_perm(user: CurrentUser, business_id: str, perm: str, db: Session):
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


def _posting_dict(p: JobPosting) -> dict:
    return {
        "id": p.id, "business_id": p.business_id, "location_id": p.location_id,
        "posted_by": p.posted_by, "title": p.title, "description": p.description,
        "role_name": p.role_name, "shift_date": p.shift_date,
        "shift_start": p.shift_start, "shift_end": p.shift_end,
        "pay_rate": p.pay_rate, "slots": p.slots, "tags": p.tags,
        "status": p.status, "created_at": p.created_at,
    }


def _req_dict(r: ShiftRequest) -> dict:
    return {
        "id": r.id, "posting_id": r.posting_id, "worker_id": r.worker_id,
        "business_id": r.business_id, "message": r.message, "status": r.status,
        "reviewed_by": r.reviewed_by, "reviewed_at": r.reviewed_at,
        "review_note": r.review_note, "created_at": r.created_at,
    }


def _training_dict(t: TrainingRequest) -> dict:
    return {
        "id": t.id, "business_id": t.business_id, "worker_id": t.worker_id,
        "skill_name": t.skill_name, "notes": t.notes, "status": t.status,
        "reviewed_by": t.reviewed_by, "reviewed_at": t.reviewed_at,
        "review_note": t.review_note, "created_at": t.created_at,
    }


def _swap_dict(s: ShiftSwapRequest) -> dict:
    return {
        "id": s.id, "business_id": s.business_id, "initiator_id": s.initiator_id,
        "peer_worker_id": s.peer_worker_id,
        "their_shift_date": s.their_shift_date, "their_shift_start": s.their_shift_start,
        "their_shift_end": s.their_shift_end, "their_shift_ref": s.their_shift_ref,
        "peer_shift_date": s.peer_shift_date, "peer_shift_start": s.peer_shift_start,
        "peer_shift_end": s.peer_shift_end,
        "message": s.message, "status": s.status,
        "peer_accepted": s.peer_accepted,
        "reviewed_by": s.reviewed_by, "reviewed_at": s.reviewed_at,
        "review_note": s.review_note, "created_at": s.created_at,
        "coverage_type": s.coverage_type,
        "covered_by_membership_id": s.covered_by_membership_id,
        "coverage_posting_id": s.coverage_posting_id,
    }


def _rule_dict(r: SwapPermissionRule) -> dict:
    return {
        "id": r.id, "business_id": r.business_id, "membership_id": r.membership_id,
        "role_name": r.role_name, "day_of_week": r.day_of_week,
        "window_start": str(r.window_start) if r.window_start else None,
        "window_end": str(r.window_end) if r.window_end else None,
        "effect": r.effect, "priority": r.priority, "note": r.note,
        "created_at": r.created_at,
    }


def _evaluate_swap_rules(
    business_id: str, membership_id: str,
    role_name: Optional[str], shift_date: Optional[str],
    shift_start: Optional[str], db: Session,
) -> Optional[SwapRuleEffect]:
    """
    Walk rules sorted by priority desc.
    First matching rule wins.  Returns None if no rule matches (needs approval).
    """
    rules = db.execute(
        select(SwapPermissionRule)
        .where(SwapPermissionRule.business_id == business_id)
        .order_by(SwapPermissionRule.priority.desc())
    ).scalars().all()

    # day-of-week from shift_date
    dow: Optional[int] = None
    if shift_date:
        try:
            dt = datetime.strptime(shift_date, "%Y-%m-%d")
            dow = dt.weekday()  # 0=Mon
        except ValueError:
            pass

    # shift start time
    t_start: Optional[time] = None
    if shift_start:
        try:
            h, m = shift_start.split(":")
            t_start = time(int(h), int(m))
        except Exception:
            pass

    for rule in rules:
        # membership filter
        if rule.membership_id and rule.membership_id != membership_id:
            continue
        # role filter
        if rule.role_name and rule.role_name != role_name:
            continue
        # day-of-week filter
        if rule.day_of_week is not None and rule.day_of_week != dow:
            continue
        # time window filter
        if rule.window_start and rule.window_end and t_start:
            if not (rule.window_start <= t_start <= rule.window_end):
                continue
        # matched
        return rule.effect

    return None  # no rule matched → needs manager approval


# ─── routers ──────────────────────────────────────────────────────────────────

public_router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])
worker_router = APIRouter(prefix="/api/v1/worker/me/marketplace", tags=["marketplace-worker"])
tenant_router = APIRouter(prefix="/api/v1/tenant/{business_id}/marketplace", tags=["marketplace-tenant"])


# ═══════════════════════════════════════════════════════════════════════════════
# PUBLIC / WORKER JOB BOARD
# ═══════════════════════════════════════════════════════════════════════════════

@public_router.get("/postings")
def search_postings(
    user: CurrentUser,
    db: Session                = Depends(get_db),
    business_id: Optional[str] = Query(None),
    q: Optional[str]           = Query(None, description="Search title/description/tags/role"),
    role_name: Optional[str]   = Query(None),
    shift_date: Optional[str]  = Query(None),
    limit: int                 = Query(50, le=200),
):
    stmt = select(JobPosting).where(
        JobPosting.status == PostingStatus.open,
        JobPosting.deleted_at.is_(None),
    )
    if business_id:
        stmt = stmt.where(JobPosting.role_name == role_name)
    if shift_date:
        stmt = stmt.where(JobPosting.shift_date == shift_date)
    if q:
        like = f"%{q}%"
        from sqlalchemy import or_
        stmt = stmt.where(or_(
            JobPosting.title.ilike(like),
            JobPosting.description.ilike(like),
            JobPosting.tags.ilike(like),
            JobPosting.role_name.ilike(like),
        ))
    rows = db.execute(stmt.order_by(JobPosting.created_at.desc()).limit(limit)).scalars().all()
    return [_posting_dict(p) for p in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER: SHIFT REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

class ShiftRequestCreate(BaseModel):
    message: Optional[str] = None


@worker_router.post("/{business_id}/shift-requests/{posting_id}", status_code=201)
def request_shift(
    business_id: str, posting_id: str, payload: ShiftRequestCreate,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_membership(user.id, business_id, db)
    posting = db.get(JobPosting, posting_id)
    if not posting or posting.business_id != business_id or posting.status != PostingStatus.open:
        raise HTTPException(404, "Posting not found or not open")

    existing = db.execute(
        select(ShiftRequest).where(
            ShiftRequest.posting_id == posting_id,
            ShiftRequest.worker_id == user.id,
            ShiftRequest.status == RequestStatus.pending,
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(409, "You already have a pending request for this posting")

    req = ShiftRequest(
        posting_id=posting_id, worker_id=user.id, business_id=business_id,
        message=payload.message, status=RequestStatus.pending,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _req_dict(req)


@worker_router.get("/{business_id}/shift-requests")
def my_shift_requests(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.execute(
        select(ShiftRequest).where(
            ShiftRequest.worker_id == user.id,
            ShiftRequest.business_id == business_id,
        ).order_by(ShiftRequest.created_at.desc())
    ).scalars().all()
    return [_req_dict(r) for r in rows]


@worker_router.delete("/{business_id}/shift-requests/{req_id}", status_code=204)
def withdraw_shift_request(
    business_id: str, req_id: str, user: CurrentUser, db: Session = Depends(get_db),
):
    req = db.get(ShiftRequest, req_id)
    if not req or req.worker_id != user.id:
        raise HTTPException(404, "Not found")
    if req.status != RequestStatus.pending:
        raise HTTPException(400, "Can only withdraw pending requests")
    req.status = RequestStatus.withdrawn
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER: TRAINING REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

class TrainingRequestCreate(BaseModel):
    skill_name: str
    notes: Optional[str] = None


@worker_router.post("/{business_id}/training-requests", status_code=201)
def request_training(
    business_id: str, payload: TrainingRequestCreate,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_membership(user.id, business_id, db)
    req = TrainingRequest(
        business_id=business_id, worker_id=user.id,
        skill_name=payload.skill_name, notes=payload.notes,
        status=RequestStatus.pending,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _training_dict(req)


@worker_router.get("/{business_id}/training-requests")
def my_training_requests(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    rows = db.execute(
        select(TrainingRequest).where(
            TrainingRequest.worker_id == user.id,
            TrainingRequest.business_id == business_id,
        ).order_by(TrainingRequest.created_at.desc())
    ).scalars().all()
    return [_training_dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# WORKER: SHIFT SWAPS
# ═══════════════════════════════════════════════════════════════════════════════

class SwapRequestCreate(BaseModel):
    their_shift_date:  Optional[str] = None
    their_shift_start: Optional[str] = None
    their_shift_end:   Optional[str] = None
    their_shift_ref:   Optional[str] = None   # schedule shift ID, if known
    peer_worker_id:    Optional[str] = None
    peer_shift_date:   Optional[str] = None
    peer_shift_start:  Optional[str] = None
    peer_shift_end:    Optional[str] = None
    message:           Optional[str] = None


@worker_router.post("/{business_id}/swap-requests", status_code=201)
def create_swap_request(
    business_id: str, payload: SwapRequestCreate,
    user: CurrentUser, db: Session = Depends(get_db),
):
    from apps.api.app.models.business import Business
    membership = _require_membership(user.id, business_id, db)

    # Evaluate swap permission rules
    effect = _evaluate_swap_rules(
        business_id=business_id,
        membership_id=membership.id,
        role_name=None,
        shift_date=payload.their_shift_date,
        shift_start=payload.their_shift_start,
        db=db,
    )

    if effect == SwapRuleEffect.deny:
        raise HTTPException(403, "Shift swaps are not permitted for your account for this shift")

    # Read business swap workflow setting (default: auto_post)
    biz = db.get(Business, business_id)
    biz_settings = json.loads(biz.settings_json or "{}") if biz else {}
    swap_workflow = biz_settings.get("swap_workflow", "auto_post")

    if swap_workflow == "auto_post":
        # Skip manager pre-approval — go straight to job board
        initial_status = SwapStatus.pending_coverage
    else:
        # manager_approval_first: manager reviews before it hits the board
        initial_status = SwapStatus.auto_approved if effect == SwapRuleEffect.allow else SwapStatus.pending

    swap = ShiftSwapRequest(
        business_id=business_id,
        initiator_id=user.id,
        peer_worker_id=payload.peer_worker_id,
        their_shift_date=payload.their_shift_date,
        their_shift_start=payload.their_shift_start,
        their_shift_end=payload.their_shift_end,
        their_shift_ref=payload.their_shift_ref,
        peer_shift_date=payload.peer_shift_date,
        peer_shift_start=payload.peer_shift_start,
        peer_shift_end=payload.peer_shift_end,
        message=payload.message,
        status=initial_status,
    )
    db.add(swap)
    db.flush()  # get swap.id before creating posting

    posting_id = None
    if initial_status == SwapStatus.pending_coverage:
        # Auto-create job board posting
        shift_date = swap.their_shift_date
        shift_start = swap.their_shift_start
        shift_end = swap.their_shift_end
        role_name = None
        location_id = None

        if swap.their_shift_ref:
            ss = db.get(ScheduleShift, swap.their_shift_ref)
            if ss:
                role_name = ss.role_name
                location_id = ss.location_id
                if ss.start_ts:
                    shift_date = ss.start_ts.strftime("%Y-%m-%d")
                    shift_start = ss.start_ts.strftime("%H:%M")
                if ss.end_ts:
                    shift_end = ss.end_ts.strftime("%H:%M")

        posting = JobPosting(
            id=str(uuid.uuid4()),
            business_id=business_id,
            location_id=location_id,
            posted_by=user.id,
            title=f"Shift Coverage — {shift_date or 'TBD'}",
            description=f"Coverage needed. {swap.message or ''}".strip(),
            role_name=role_name,
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=shift_end,
            slots=1,
            swap_request_id=swap.id,
            eligibility_rules=json.dumps({"required_role": role_name} if role_name else {}),
            status=PostingStatus.open,
        )
        db.add(posting)
        swap.coverage_type = "job_board"
        swap.coverage_posting_id = posting.id
        posting_id = posting.id

    db.commit()
    db.refresh(swap)
    result = _swap_dict(swap)
    if posting_id:
        result["posting_id"] = posting_id
    return result


@worker_router.get("/{business_id}/swap-requests")
def my_swap_requests(business_id: str, user: CurrentUser, db: Session = Depends(get_db)):
    from sqlalchemy import or_
    rows = db.execute(
        select(ShiftSwapRequest).where(
            ShiftSwapRequest.business_id == business_id,
            or_(
                ShiftSwapRequest.initiator_id == user.id,
                ShiftSwapRequest.peer_worker_id == user.id,
            )
        ).order_by(ShiftSwapRequest.created_at.desc())
    ).scalars().all()
    return [_swap_dict(s) for s in rows]


@worker_router.post("/{business_id}/swap-requests/{swap_id}/respond")
def respond_to_swap(
    business_id: str, swap_id: str,
    accept: bool, user: CurrentUser, db: Session = Depends(get_db),
):
    """Peer worker accepts or declines a targeted swap request."""
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.business_id != business_id:
        raise HTTPException(404, "Swap not found")
    if swap.peer_worker_id != user.id:
        raise HTTPException(403, "Not the target peer for this swap")
    if swap.status not in (SwapStatus.pending, SwapStatus.awaiting_peer):
        raise HTTPException(400, f"Swap is already {swap.status}")

    swap.peer_accepted = accept
    swap.status = SwapStatus.approved if accept else SwapStatus.denied
    db.commit()
    db.refresh(swap)
    return _swap_dict(swap)


@worker_router.post("/{business_id}/swap-requests/{swap_id}/initiator-approve")
def initiator_approve_swap(
    business_id: str, swap_id: str,
    user: CurrentUser, db: Session = Depends(get_db),
):
    """
    Initiator confirms they still want to proceed with the swap.
    Moves status: pending → awaiting_peer (notifies peer to respond).
    Only valid when a peer_worker_id is set (targeted swap).
    """
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.business_id != business_id:
        raise HTTPException(404, "Swap not found")
    if swap.initiator_id != user.id:
        raise HTTPException(403, "Only the initiator may approve this step")
    if swap.status != SwapStatus.pending:
        raise HTTPException(400, f"Swap is in state '{swap.status}' — expected 'pending'")
    if not swap.peer_worker_id:
        raise HTTPException(400, "Open-offer swaps do not require initiator approval")

    # Evaluate swap rules again; deny rules block at this point too
    effect = _evaluate_swap_rules(
        business_id,
        user.id,
        None,
        swap.their_shift_date,
        swap.their_shift_start,
        db,
    )
    if effect == SwapRuleEffect.deny:
        raise HTTPException(403, "Shift swaps are not permitted under current rules")

    swap.status = SwapStatus.awaiting_peer
    db.commit()
    db.refresh(swap)
    return _swap_dict(swap)


@worker_router.delete("/{business_id}/swap-requests/{swap_id}", status_code=204)
def withdraw_swap(
    business_id: str, swap_id: str, user: CurrentUser, db: Session = Depends(get_db),
):
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.initiator_id != user.id:
        raise HTTPException(404, "Not found")
    if swap.status not in (SwapStatus.pending, SwapStatus.awaiting_peer):
        raise HTTPException(400, "Cannot withdraw a finalised swap")
    swap.status = SwapStatus.withdrawn
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: JOB POSTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class PostingCreate(BaseModel):
    title:       str
    description: Optional[str] = None
    role_name:   Optional[str] = None
    location_id: Optional[str] = None
    shift_date:  Optional[str] = None
    shift_start: Optional[str] = None
    shift_end:   Optional[str] = None
    pay_rate:    Optional[str] = None
    slots:       int = 1
    tags:        Optional[str] = None  # comma-separated


@tenant_router.post("/postings", status_code=201)
def create_posting(
    business_id: str, payload: PostingCreate,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    p = JobPosting(
        business_id=business_id, posted_by=user.id,
        **payload.model_dump()
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return _posting_dict(p)


@tenant_router.get("/postings")
def list_postings(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
    status: Optional[str] = None,
):
    _require_perm(user, business_id, "marketplace:read", db)
    stmt = select(JobPosting).where(
        JobPosting.business_id == business_id, JobPosting.deleted_at.is_(None)
    )
    if status:
        try:
            stmt = stmt.where(JobPosting.status == PostingStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    rows = db.execute(stmt.order_by(JobPosting.created_at.desc())).scalars().all()
    return [_posting_dict(p) for p in rows]


@tenant_router.patch("/postings/{posting_id}")
def update_posting(
    business_id: str, posting_id: str,
    payload: dict, user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    p = db.get(JobPosting, posting_id)
    if not p or p.business_id != business_id or p.deleted_at:
        raise HTTPException(404, "Posting not found")
    allowed = {"title","description","role_name","shift_date","shift_start","shift_end",
               "pay_rate","slots","tags","status"}
    for k, v in payload.items():
        if k in allowed:
            setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return _posting_dict(p)


@tenant_router.delete("/postings/{posting_id}", status_code=204)
def delete_posting(
    business_id: str, posting_id: str,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    p = db.get(JobPosting, posting_id)
    if not p or p.business_id != business_id:
        raise HTTPException(404, "Posting not found")
    p.deleted_at = _now()
    p.status = PostingStatus.cancelled
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: REVIEW SHIFT REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

class ReviewPayload(BaseModel):
    status:      str
    review_note: Optional[str] = None


@tenant_router.get("/shift-requests")
def list_shift_requests(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
    status: Optional[str] = None,
):
    _require_perm(user, business_id, "marketplace:manage", db)
    stmt = select(ShiftRequest).where(ShiftRequest.business_id == business_id)
    if status:
        try:
            stmt = stmt.where(ShiftRequest.status == RequestStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    rows = db.execute(stmt.order_by(ShiftRequest.created_at.desc())).scalars().all()
    return [_req_dict(r) for r in rows]


@tenant_router.patch("/shift-requests/{req_id}")
def review_shift_request(
    business_id: str, req_id: str, payload: ReviewPayload,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    req = db.get(ShiftRequest, req_id)
    if not req or req.business_id != business_id:
        raise HTTPException(404, "Request not found")
    try:
        req.status = RequestStatus(payload.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status '{payload.status}'")
    req.reviewed_by = user.id
    req.reviewed_at = _now()
    req.review_note = payload.review_note
    # If approved, check if posting slots are filled; also complete linked swap
    if req.status == RequestStatus.approved:
        posting = db.get(JobPosting, req.posting_id)
        if posting:
            approved_count = db.execute(
                select(ShiftRequest).where(
                    ShiftRequest.posting_id == req.posting_id,
                    ShiftRequest.status == RequestStatus.approved,
                )
            ).scalars().all()
            if len(approved_count) >= posting.slots:
                posting.status = PostingStatus.filled
            # If this posting was created for a swap, complete the swap
            if posting.swap_request_id:
                # Find the claiming worker's membership
                claiming_mem = db.execute(
                    select(Membership).where(
                        Membership.user_id == req.worker_id,
                        Membership.business_id == business_id,
                    )
                ).scalar_one_or_none()
                if claiming_mem:
                    _complete_swap_if_linked(req.posting_id, claiming_mem.id, business_id, db)
    db.commit()
    db.refresh(req)
    return _req_dict(req)


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: REVIEW TRAINING REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

@tenant_router.get("/training-requests")
def list_training_requests(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
    status: Optional[str] = None,
):
    _require_perm(user, business_id, "marketplace:manage", db)
    stmt = select(TrainingRequest).where(TrainingRequest.business_id == business_id)
    if status:
        try:
            stmt = stmt.where(TrainingRequest.status == RequestStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    rows = db.execute(stmt.order_by(TrainingRequest.created_at.desc())).scalars().all()
    return [_training_dict(r) for r in rows]


@tenant_router.patch("/training-requests/{req_id}")
def review_training_request(
    business_id: str, req_id: str, payload: ReviewPayload,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    req = db.get(TrainingRequest, req_id)
    if not req or req.business_id != business_id:
        raise HTTPException(404, "Not found")
    try:
        req.status = RequestStatus(payload.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status '{payload.status}'")
    req.reviewed_by = user.id
    req.reviewed_at = _now()
    req.review_note = payload.review_note
    db.commit()
    db.refresh(req)
    return _training_dict(req)


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: REVIEW SWAP REQUESTS
# ═══════════════════════════════════════════════════════════════════════════════

@tenant_router.get("/swap-requests")
def list_swap_requests(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
    status: Optional[str] = None,
):
    _require_perm(user, business_id, "marketplace:manage", db)
    stmt = select(ShiftSwapRequest).where(ShiftSwapRequest.business_id == business_id)
    if status:
        try:
            stmt = stmt.where(ShiftSwapRequest.status == SwapStatus(status))
        except ValueError:
            raise HTTPException(400, f"Invalid status: {status}")
    rows = db.execute(stmt.order_by(ShiftSwapRequest.created_at.desc())).scalars().all()
    return [_swap_dict(r) for r in rows]


@tenant_router.get("/notification-counts")
def tenant_notification_counts(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
):
    """Return pending item counts for sidebar notification badges."""
    _require_perm(user, business_id, "marketplace:manage", db)

    def _count(model, *filters):
        return db.execute(select(func.count()).select_from(model).where(*filters)).scalar_one()

    swap_requests = _count(
        ShiftSwapRequest,
        ShiftSwapRequest.business_id == business_id,
        ShiftSwapRequest.status.in_([SwapStatus.pending, SwapStatus.awaiting_peer]),
    )
    shift_requests = _count(
        ShiftRequest,
        ShiftRequest.business_id == business_id,
        ShiftRequest.status == RequestStatus.pending,
    )
    training_requests = _count(
        TrainingRequest,
        TrainingRequest.business_id == business_id,
        TrainingRequest.status == RequestStatus.pending,
    )
    return {
        "swap_requests":    swap_requests,
        "shift_requests":   shift_requests + training_requests,
    }


@worker_router.get("/{business_id}/notification-counts")
def worker_notification_counts(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
):
    """Counts for the worker's My Work badge (swaps awaiting their response)."""
    awaiting = db.execute(
        select(func.count()).select_from(ShiftSwapRequest).where(
            ShiftSwapRequest.business_id == business_id,
            ShiftSwapRequest.peer_worker_id == user.id,
            ShiftSwapRequest.status == SwapStatus.awaiting_peer,
        )
    ).scalar_one()
    pending_mine = db.execute(
        select(func.count()).select_from(ShiftSwapRequest).where(
            ShiftSwapRequest.business_id == business_id,
            ShiftSwapRequest.initiator_id == user.id,
            ShiftSwapRequest.status == SwapStatus.pending,
        )
    ).scalar_one()
    return {"my_work": awaiting + pending_mine}


@tenant_router.patch("/swap-requests/{swap_id}")
def review_swap_request(
    business_id: str, swap_id: str, payload: ReviewPayload,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.business_id != business_id:
        raise HTTPException(404, "Not found")
    try:
        new_status = SwapStatus(payload.status)
    except ValueError:
        raise HTTPException(400, f"Invalid status '{payload.status}'")
    # When manager approves a swap, move to pending_coverage and auto-post to job board
    if new_status in (SwapStatus.approved, SwapStatus.auto_approved):
        new_status = SwapStatus.pending_coverage
    swap.status = new_status
    swap.reviewed_by = user.id
    swap.reviewed_at = _now()
    swap.review_note = payload.review_note

    posting_id = None
    if new_status == SwapStatus.pending_coverage and not swap.coverage_posting_id:
        # Auto-create a job board posting for this shift
        shift_date = swap.their_shift_date
        shift_start = swap.their_shift_start
        shift_end = swap.their_shift_end
        role_name = None
        location_id = None

        if swap.their_shift_ref:
            ss = db.get(ScheduleShift, swap.their_shift_ref)
            if ss:
                role_name = ss.role_name
                location_id = ss.location_id
                if ss.start_ts:
                    shift_date = ss.start_ts.strftime("%Y-%m-%d")
                    shift_start = ss.start_ts.strftime("%H:%M")
                if ss.end_ts:
                    shift_end = ss.end_ts.strftime("%H:%M")

        posting = JobPosting(
            id=str(uuid.uuid4()),
            business_id=business_id,
            location_id=location_id,
            posted_by=user.id,
            title=f"Shift Coverage — {shift_date or 'TBD'}",
            description=f"Coverage needed for an approved swap request. {swap.message or ''}".strip(),
            role_name=role_name,
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=shift_end,
            slots=1,
            swap_request_id=swap.id,
            eligibility_rules=json.dumps({"required_role": role_name} if role_name else {}),
            status=PostingStatus.open,
        )
        db.add(posting)
        swap.coverage_type = "job_board"
        swap.coverage_posting_id = posting.id
        posting_id = posting.id

    db.commit()
    db.refresh(swap)
    result = _swap_dict(swap)
    if posting_id:
        result["posting_id"] = posting_id
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: SWAP PERMISSION RULES
# ═══════════════════════════════════════════════════════════════════════════════

class SwapRuleCreate(BaseModel):
    membership_id: Optional[str] = None   # NULL = applies to all employees
    role_name:     Optional[str] = None
    day_of_week:   Optional[int] = None   # 0=Mon–6=Sun
    window_start:  Optional[str] = None   # "HH:MM"
    window_end:    Optional[str] = None   # "HH:MM"
    effect:        str = "allow"          # allow | deny
    priority:      int = 10
    note:          Optional[str] = None


def _parse_time(s: Optional[str]) -> Optional[time]:
    if not s:
        return None
    try:
        h, m = s.split(":")
        return time(int(h), int(m))
    except Exception:
        raise HTTPException(400, f"Invalid time format '{s}', use HH:MM")


@tenant_router.get("/swap-rules")
def list_swap_rules(
    business_id: str, user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    rows = db.execute(
        select(SwapPermissionRule)
        .where(SwapPermissionRule.business_id == business_id)
        .order_by(SwapPermissionRule.priority.desc())
    ).scalars().all()
    return [_rule_dict(r) for r in rows]


@tenant_router.post("/swap-rules", status_code=201)
def create_swap_rule(
    business_id: str, payload: SwapRuleCreate,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    try:
        effect = SwapRuleEffect(payload.effect)
    except ValueError:
        raise HTTPException(400, f"Invalid effect '{payload.effect}', use allow or deny")

    rule = SwapPermissionRule(
        business_id=business_id,
        membership_id=payload.membership_id,
        role_name=payload.role_name,
        day_of_week=payload.day_of_week,
        window_start=_parse_time(payload.window_start),
        window_end=_parse_time(payload.window_end),
        effect=effect,
        priority=payload.priority,
        note=payload.note,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return _rule_dict(rule)


@tenant_router.delete("/swap-rules/{rule_id}", status_code=204)
def delete_swap_rule(
    business_id: str, rule_id: str,
    user: CurrentUser, db: Session = Depends(get_db),
):
    _require_perm(user, business_id, "marketplace:manage", db)
    rule = db.get(SwapPermissionRule, rule_id)
    if not rule or rule.business_id != business_id:
        raise HTTPException(404, "Rule not found")
    db.delete(rule)
    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TENANT: SWAP COVERAGE ARRANGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def _eligible_workers_for_swap(swap: ShiftSwapRequest, business_id: str, db: Session) -> list[dict]:
    """
    Return members eligible to cover the swap shift.
    Checks: active membership, role qualification, availability, no schedule conflict.
    """
    import json as _json
    from datetime import datetime as _dt

    shift_date = swap.their_shift_date   # "YYYY-MM-DD"
    shift_start = swap.their_shift_start  # "HH:MM"
    shift_end = swap.their_shift_end
    role_needed = None

    # Try to get role from the actual shift if their_shift_ref is set
    shift_start_hour = None
    shift_end_hour = None
    if swap.their_shift_ref:
        ss = db.get(ScheduleShift, swap.their_shift_ref)
        if ss:
            role_needed = ss.role_name
            if ss.start_ts:
                shift_start_hour = ss.start_ts.hour + ss.start_ts.minute / 60
            if ss.end_ts:
                shift_end_hour = ss.end_ts.hour + ss.end_ts.minute / 60
    
    if shift_start and shift_start_hour is None:
        try:
            h, m = shift_start.split(":")
            shift_start_hour = int(h) + int(m) / 60
        except Exception:
            pass
    if shift_end and shift_end_hour is None:
        try:
            h, m = shift_end.split(":")
            shift_end_hour = int(h) + int(m) / 60
        except Exception:
            pass

    # Weekday from shift_date (0=Mon)
    day_of_week = None
    if shift_date:
        try:
            day_of_week = _dt.fromisoformat(shift_date).weekday()
        except Exception:
            pass

    # All active members (excluding initiator)
    members = db.execute(
        select(Membership).where(
            Membership.business_id == business_id,
            Membership.status == MembershipStatus.active,
            Membership.user_id != swap.initiator_id,
        )
    ).scalars().all()

    results = []
    for m in members:
        reason_ok = []
        reason_fail = []

        # Check worker profile for role qualification
        wp = db.execute(
            select(WorkerProfile).where(WorkerProfile.membership_id == m.id)
        ).scalar_one_or_none()

        role_qualified = True
        if role_needed and wp and wp.qualified_roles:
            try:
                qr = _json.loads(wp.qualified_roles)
                role_qualified = role_needed in qr
            except Exception:
                pass
        if role_needed:
            (reason_ok if role_qualified else reason_fail).append(
                f"Role: {'✓' if role_qualified else '✗'} {role_needed}"
            )

        # Check availability
        avail_ok = True
        if day_of_week is not None and shift_start_hour is not None and shift_end_hour is not None:
            avail_rows = db.execute(
                select(WorkerAvailability).where(
                    WorkerAvailability.membership_id == m.id,
                    WorkerAvailability.day_of_week == day_of_week,
                )
            ).scalars().all()
            if avail_rows:
                avail_ok = any(
                    a.start_hour <= shift_start_hour and a.end_hour >= shift_end_hour
                    for a in avail_rows
                )
                (reason_ok if avail_ok else reason_fail).append(
                    f"Availability: {'✓' if avail_ok else '✗'}"
                )
            else:
                reason_ok.append("Availability: ✓ (none set — open)")

        # Check schedule conflicts
        conflict = False
        if swap.their_shift_ref:
            ref_shift = db.get(ScheduleShift, swap.their_shift_ref)
            if ref_shift and ref_shift.start_ts and ref_shift.end_ts:
                overlapping = db.execute(
                    select(ScheduleAssignment)
                    .join(ScheduleShift, ScheduleShift.id == ScheduleAssignment.shift_id)
                    .where(
                        ScheduleAssignment.membership_id == m.id,
                        ScheduleShift.start_ts < ref_shift.end_ts,
                        ScheduleShift.end_ts > ref_shift.start_ts,
                    )
                ).scalars().first()
                conflict = overlapping is not None
                (reason_fail if conflict else reason_ok).append(
                    f"Conflicts: {'✗ has overlap' if conflict else '✓ none'}"
                )

        eligible = role_qualified and avail_ok and not conflict
        results.append({
            "membership_id": m.id,
            "user_id": m.user_id,
            "job_title": wp.job_title if wp else None,
            "qualified_roles": json.loads(wp.qualified_roles) if wp and wp.qualified_roles else [],
            "eligible": eligible,
            "reasons": reason_ok + reason_fail,
        })

    results.sort(key=lambda x: (not x["eligible"],))
    return results


@tenant_router.get("/swap-requests/{swap_id}/eligible-workers")
def get_eligible_workers(
    business_id: str, swap_id: str,
    user: CurrentUser, db: Session = Depends(get_db),
):
    """Return all active members with eligibility status for covering this swap."""
    _require_perm(user, business_id, "marketplace:manage", db)
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.business_id != business_id:
        raise HTTPException(404, "Swap request not found")
    return _eligible_workers_for_swap(swap, business_id, db)


class ArrangeCoveragePayload(BaseModel):
    type: str                        # "manual" or "job_board"
    membership_id: Optional[str] = None    # for manual
    # job_board options
    title: Optional[str] = None
    description: Optional[str] = None
    pay_rate: Optional[str] = None
    eligibility_rules: Optional[dict] = None   # {required_role, require_availability, require_location_match}


@tenant_router.post("/swap-requests/{swap_id}/arrange-coverage")
def arrange_coverage(
    business_id: str, swap_id: str, payload: ArrangeCoveragePayload,
    user: CurrentUser, db: Session = Depends(get_db),
):
    """
    Arrange coverage for an approved swap:
    - type=manual: directly assign membership_id to the shift, mark swap completed
    - type=job_board: create a JobPosting linked to this swap with eligibility rules
    """
    _require_perm(user, business_id, "marketplace:manage", db)
    swap = db.get(ShiftSwapRequest, swap_id)
    if not swap or swap.business_id != business_id:
        raise HTTPException(404, "Swap request not found")
    if swap.status not in (SwapStatus.pending_coverage,):
        raise HTTPException(400, f"Swap is not in pending_coverage state (current: {swap.status})")

    if payload.type == "manual":
        if not payload.membership_id:
            raise HTTPException(400, "membership_id required for manual coverage")
        # Find and transfer the shift assignment
        if swap.their_shift_ref:
            # Get initiator's membership
            initiator_mem = db.execute(
                select(Membership).where(
                    Membership.user_id == swap.initiator_id,
                    Membership.business_id == business_id,
                )
            ).scalar_one_or_none()

            existing = db.execute(
                select(ScheduleAssignment).where(
                    ScheduleAssignment.shift_id == swap.their_shift_ref,
                    ScheduleAssignment.membership_id == (initiator_mem.id if initiator_mem else None),
                )
            ).scalar_one_or_none()

            if existing:
                existing.membership_id = payload.membership_id
            else:
                # Create a new assignment for the new worker
                db.add(ScheduleAssignment(
                    id=str(uuid.uuid4()),
                    shift_id=swap.their_shift_ref,
                    membership_id=payload.membership_id,
                    status="assigned",
                ))

        swap.coverage_type = "manual"
        swap.covered_by_membership_id = payload.membership_id
        swap.status = SwapStatus.completed
        db.commit()
        db.refresh(swap)
        return _swap_dict(swap)

    elif payload.type == "job_board":
        # Derive shift details from the swap or its shift reference
        shift_date = swap.their_shift_date
        shift_start = swap.their_shift_start
        shift_end = swap.their_shift_end
        role_name = None
        location_id = None

        if swap.their_shift_ref:
            ss = db.get(ScheduleShift, swap.their_shift_ref)
            if ss:
                role_name = ss.role_name
                location_id = ss.location_id
                if ss.start_ts:
                    shift_date = ss.start_ts.strftime("%Y-%m-%d")
                    shift_start = ss.start_ts.strftime("%H:%M")
                if ss.end_ts:
                    shift_end = ss.end_ts.strftime("%H:%M")

        rules = payload.eligibility_rules or {}
        if role_name and "required_role" not in rules:
            rules["required_role"] = role_name

        posting = JobPosting(
            id=str(uuid.uuid4()),
            business_id=business_id,
            location_id=location_id,
            posted_by=user.id,
            title=payload.title or f"Shift Coverage — {shift_date or 'TBD'}",
            description=payload.description or f"Coverage needed for a swap request. {swap.message or ''}".strip(),
            role_name=rules.get("required_role", role_name),
            shift_date=shift_date,
            shift_start=shift_start,
            shift_end=shift_end,
            pay_rate=payload.pay_rate,
            slots=1,
            swap_request_id=swap_id,
            eligibility_rules=json.dumps(rules),
            status=PostingStatus.open,
        )
        db.add(posting)
        swap.coverage_type = "job_board"
        swap.coverage_posting_id = posting.id
        db.commit()
        db.refresh(swap)
        return {**_swap_dict(swap), "posting_id": posting.id}

    else:
        raise HTTPException(400, "type must be 'manual' or 'job_board'")


# ═══════════════════════════════════════════════════════════════════════════════
# JOB BOARD CLAIM → COMPLETE SWAP
# (called from within the existing shift-request approval endpoint)
# ═══════════════════════════════════════════════════════════════════════════════

def _complete_swap_if_linked(posting_id: str, claiming_membership_id: str, business_id: str, db: Session):
    """
    If a job posting was created for a swap, and a ShiftRequest on that posting
    is approved, transfer the shift assignment and mark the swap as completed.
    """
    posting = db.get(JobPosting, posting_id)
    if not posting or not posting.swap_request_id:
        return
    swap = db.get(ShiftSwapRequest, posting.swap_request_id)
    if not swap or swap.status != SwapStatus.pending_coverage:
        return

    # Transfer the shift assignment
    if swap.their_shift_ref:
        initiator_mem = db.execute(
            select(Membership).where(
                Membership.user_id == swap.initiator_id,
                Membership.business_id == business_id,
            )
        ).scalar_one_or_none()

        existing = db.execute(
            select(ScheduleAssignment).where(
                ScheduleAssignment.shift_id == swap.their_shift_ref,
                ScheduleAssignment.membership_id == (initiator_mem.id if initiator_mem else None),
            )
        ).scalar_one_or_none()

        if existing:
            existing.membership_id = claiming_membership_id
        else:
            db.add(ScheduleAssignment(
                id=str(uuid.uuid4()),
                shift_id=swap.their_shift_ref,
                membership_id=claiming_membership_id,
                status="assigned",
            ))

    swap.covered_by_membership_id = claiming_membership_id
    swap.status = SwapStatus.completed
    posting.status = PostingStatus.filled
