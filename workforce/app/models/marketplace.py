"""
Shift Marketplace models:
  JobPosting         — business posts an open shift / job for workers to claim
  ShiftRequest       — worker requests a shift (from a JobPosting or arbitrary)
  TrainingRequest    — worker requests training for a skill / certification
  ShiftSwapRequest   — worker proposes to swap their shift with another worker
  SwapPermissionRule — granular rule: allow/deny a membership to auto-swap shifts
                       constrained by day-of-week, time window, and role match
"""
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text, Time,
)
from sqlalchemy.orm import relationship
from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class PostingStatus(str, enum.Enum):
    open      = "open"
    filled    = "filled"
    cancelled = "cancelled"


class RequestStatus(str, enum.Enum):
    pending  = "pending"
    approved = "approved"
    denied   = "denied"
    withdrawn = "withdrawn"


class SwapStatus(str, enum.Enum):
    pending          = "pending"
    awaiting_peer    = "awaiting_peer"   # initiator approved, waiting other worker
    approved         = "approved"
    denied           = "denied"
    auto_approved    = "auto_approved"
    withdrawn        = "withdrawn"
    pending_coverage = "pending_coverage"  # approved; manager arranging coverage
    completed        = "completed"         # coverage confirmed, shift transferred


class SwapRuleEffect(str, enum.Enum):
    allow = "allow"   # auto-approve without manager review
    deny  = "deny"    # prevent swap entirely


class JobPosting(Base):
    __tablename__ = "job_postings"

    id          = Column(String, primary_key=True, default=_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    location_id = Column(String, ForeignKey("locations.id"), nullable=True)
    posted_by   = Column(String, ForeignKey("users.id"), nullable=False)

    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    role_name   = Column(String(100), nullable=True)   # e.g. "Barista", "Cashier"
    shift_date  = Column(String(20), nullable=True)    # ISO date "2026-03-01"
    shift_start = Column(String(10), nullable=True)    # "09:00"
    shift_end   = Column(String(10), nullable=True)    # "17:00"
    pay_rate    = Column(String(50), nullable=True)    # free-text "$18/hr"
    slots       = Column(Integer, default=1)           # how many workers needed
    tags        = Column(String(500), nullable=True)   # comma-separated keywords

    # Optional link to a swap request that generated this posting
    swap_request_id    = Column(String, ForeignKey("shift_swap_requests.id"), nullable=True)
    eligibility_rules  = Column(Text, nullable=True)   # JSON: {required_role, require_availability, require_location_match, max_weekly_hours}

    status      = Column(Enum(PostingStatus), default=PostingStatus.open, nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at  = Column(DateTime, nullable=True)

    requests    = relationship("ShiftRequest", back_populates="posting", lazy="dynamic")


class ShiftRequest(Base):
    __tablename__ = "shift_requests"

    id          = Column(String, primary_key=True, default=_uuid)
    posting_id  = Column(String, ForeignKey("job_postings.id"), nullable=False, index=True)
    worker_id   = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    business_id = Column(String, nullable=False, index=True)  # denormalized for easy scope

    message     = Column(Text, nullable=True)
    status      = Column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    posting     = relationship("JobPosting", back_populates="requests")


class TrainingRequest(Base):
    __tablename__ = "training_requests"

    id          = Column(String, primary_key=True, default=_uuid)
    business_id = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    worker_id   = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    skill_name  = Column(String(200), nullable=False)
    notes       = Column(Text, nullable=True)
    status      = Column(Enum(RequestStatus), default=RequestStatus.pending, nullable=False)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ShiftSwapRequest(Base):
    """
    Worker A wants to swap their shift (their_shift_id / their_shift_date)
    with Worker B's shift (peer_shift_id / peer_shift_date), or just offer
    theirs for any taker (peer_worker_id may be NULL for open offers).
    """
    __tablename__ = "shift_swap_requests"

    id               = Column(String, primary_key=True, default=_uuid)
    business_id      = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    initiator_id     = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    peer_worker_id   = Column(String, ForeignKey("users.id"), nullable=True)   # NULL = open offer

    # Initiator's shift details
    their_shift_date  = Column(String(20), nullable=True)
    their_shift_start = Column(String(10), nullable=True)
    their_shift_end   = Column(String(10), nullable=True)
    their_shift_ref   = Column(String, nullable=True)   # FK to a future Schedule table (optional)

    # Desired peer shift details (nullable for open offers)
    peer_shift_date   = Column(String(20), nullable=True)
    peer_shift_start  = Column(String(10), nullable=True)
    peer_shift_end    = Column(String(10), nullable=True)
    peer_shift_ref    = Column(String, nullable=True)

    message           = Column(Text, nullable=True)
    status      = Column(Enum(SwapStatus), default=SwapStatus.pending, nullable=False)
    peer_accepted     = Column(Boolean, nullable=True)   # True/False/None (pending)
    reviewed_by       = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at       = Column(DateTime, nullable=True)
    review_note       = Column(Text, nullable=True)
    created_at        = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Coverage tracking (set when manager arranges coverage)
    coverage_type            = Column(String(20), nullable=True)   # 'manual' or 'job_board'
    covered_by_membership_id = Column(String, ForeignKey("memberships.id"), nullable=True)
    coverage_posting_id      = Column(String, ForeignKey("job_postings.id", use_alter=True, name="fk_swap_coverage_posting"), nullable=True)


class SwapPermissionRule(Base):
    """
    Granular rule scoped to a business (and optionally a membership / location).
    effect=allow  → worker can auto-swap without manager approval
    effect=deny   → worker is blocked from swapping entirely

    Constraints (all nullable — NULL means "any"):
      membership_id    — specific employee (NULL = all employees)
      role_name        — only for shifts of this role
      day_of_week      — 0=Mon…6=Sun (NULL = any day)
      window_start/end — time-of-day window the shift must fall within
    """
    __tablename__ = "swap_permission_rules"

    id            = Column(String, primary_key=True, default=_uuid)
    business_id   = Column(String, ForeignKey("businesses.id"), nullable=False, index=True)
    membership_id = Column(String, ForeignKey("memberships.id"), nullable=True)  # NULL = all
    role_name     = Column(String(100), nullable=True)
    day_of_week   = Column(Integer, nullable=True)    # 0–6, NULL = any
    window_start  = Column(Time, nullable=True)       # e.g. 08:00
    window_end    = Column(Time, nullable=True)       # e.g. 17:00
    effect        = Column(Enum(SwapRuleEffect), default=SwapRuleEffect.allow, nullable=False)
    priority      = Column(Integer, default=10)       # higher = evaluated first; deny beats allow at same priority
    note          = Column(String(300), nullable=True)
    created_at    = Column(DateTime, default=lambda: datetime.now(timezone.utc))
