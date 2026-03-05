"""
HKops — Housekeeping Operations models.

Entities:
  HKRoom        — physical room/unit tracked per business + location
  HKTaskType    — configurable catalogue of task types per business
  HKTask        — task instance assigned to a room and (optionally) a worker
  HKInspection  — inspection result attached to a completed HKTask
"""
import enum
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────

class RoomStatus(str, enum.Enum):
    dirty        = "dirty"
    clean        = "clean"
    inspected    = "inspected"
    out_of_order = "out_of_order"
    do_not_disturb = "do_not_disturb"


class TaskStatus(str, enum.Enum):
    pending     = "pending"
    in_progress = "in_progress"
    completed   = "completed"
    skipped     = "skipped"
    flagged     = "flagged"       # needs supervisor attention


class TaskPriority(str, enum.Enum):
    low    = "low"
    normal = "normal"
    high   = "high"
    urgent = "urgent"


class InspectionResult(str, enum.Enum):
    pass_      = "pass"
    fail       = "fail"
    conditional = "conditional"  # passed with minor issues noted


# ── Models ────────────────────────────────────────────────────────────────────

class HKRoom(UUIDMixin, TimestampMixin, Base):
    """A physical room or unit tracked by the HK dept."""
    __tablename__ = "hk_rooms"

    business_id = Column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True, index=True)

    room_number = Column(String(20), nullable=False)   # e.g. "101", "A-203"
    floor       = Column(String(10), nullable=True)    # e.g. "1", "Mezzanine"
    wing        = Column(String(50), nullable=True)    # e.g. "East Wing", "Building B"
    room_type   = Column(String(50), nullable=True)    # e.g. "King Suite", "Double", "Conference"

    status      = Column(Enum(RoomStatus), default=RoomStatus.dirty, nullable=False)
    notes       = Column(Text, nullable=True)          # freeform manager notes
    is_active   = Column(Boolean, default=True, nullable=False)

    tasks        = relationship("HKTask", back_populates="room", lazy="dynamic")


class HKTaskType(UUIDMixin, TimestampMixin, Base):
    """Configurable task type catalogue per business (checkout clean, deep clean, etc.)."""
    __tablename__ = "hk_task_types"

    business_id              = Column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)
    name                     = Column(String(100), nullable=False)          # e.g. "Checkout Clean"
    description              = Column(Text, nullable=True)
    default_duration_minutes = Column(Integer, default=30, nullable=False)  # expected task length
    requires_inspection      = Column(Boolean, default=False, nullable=False)
    is_active                = Column(Boolean, default=True, nullable=False)

    tasks = relationship("HKTask", back_populates="task_type", lazy="dynamic")


class HKTask(UUIDMixin, TimestampMixin, Base):
    """A housekeeping task instance: room × task_type × worker × time."""
    __tablename__ = "hk_tasks"

    business_id  = Column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)
    room_id      = Column(String(36), ForeignKey("hk_rooms.id"), nullable=False, index=True)
    task_type_id = Column(String(36), ForeignKey("hk_task_types.id"), nullable=False, index=True)
    assigned_to  = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)  # worker user_id
    created_by   = Column(String(36), ForeignKey("users.id"), nullable=False)

    status       = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False, index=True)
    priority     = Column(Enum(TaskPriority), default=TaskPriority.normal, nullable=False)

    # Scheduling window
    scheduled_date  = Column(String(20), nullable=True)   # ISO date "2026-03-01"
    scheduled_start = Column(String(10), nullable=True)   # "09:00"
    scheduled_end   = Column(String(10), nullable=True)   # "10:00"

    # Timestamps set by worker actions
    started_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at  = Column(DateTime(timezone=True), nullable=True)

    notes            = Column(Text, nullable=True)   # worker notes on completion
    supervisor_notes = Column(Text, nullable=True)   # manager/supervisor overrides

    room        = relationship("HKRoom", back_populates="tasks")
    task_type   = relationship("HKTaskType", back_populates="tasks")
    inspection  = relationship("HKInspection", back_populates="task", uselist=False)


class HKInspection(UUIDMixin, TimestampMixin, Base):
    """Inspection result attached to a completed HKTask."""
    __tablename__ = "hk_inspections"

    task_id      = Column(String(36), ForeignKey("hk_tasks.id"), nullable=False, unique=True)
    business_id  = Column(String(36), ForeignKey("businesses.id"), nullable=False, index=True)
    inspector_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    result  = Column(Enum(InspectionResult), nullable=False)
    score   = Column(Integer, nullable=True)    # 0–100 optional numeric score
    issues  = Column(Text, nullable=True)       # JSON list of issue strings
    notes   = Column(Text, nullable=True)

    inspected_at = Column(DateTime(timezone=True), default=_now, nullable=False)

    task = relationship("HKTask", back_populates="inspection")

    @property
    def issues_list(self) -> list[str]:
        if not self.issues:
            return []
        try:
            return json.loads(self.issues)
        except (ValueError, TypeError):
            return []
