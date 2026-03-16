"""
Schedule models — ScheduleShift, ScheduleAssignment, ScheduleRule.
These integrate with the Membership (identity) system, replacing the legacy
Employee-based Shift/ShiftAssignment models for tenant scheduling.
"""
import enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.workforce.workforce.app.models.base import Base, TimestampMixin, UUIDMixin


class ShiftStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"


class AssignmentStatus(str, enum.Enum):
    assigned = "assigned"
    confirmed = "confirmed"
    declined = "declined"
    no_show = "no_show"


class ScheduleShift(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "schedule_shifts"

    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    role_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    start_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    needed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ShiftStatus] = mapped_column(
        Enum(ShiftStatus, name="sched_shift_status"),
        nullable=False,
        default=ShiftStatus.draft,
    )
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)  # e.g. "#6366f1"
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    assignments: Mapped[list["ScheduleAssignment"]] = relationship(
        "ScheduleAssignment", back_populates="shift", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_sched_shift_end_after_start"),
        Index("ix_sched_shifts_biz_window", "business_id", "start_ts", "end_ts"),
    )


class ScheduleAssignment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "schedule_assignments"

    shift_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("schedule_shifts.id", ondelete="CASCADE"), nullable=False
    )
    membership_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="sched_assignment_status"),
        nullable=False,
        default=AssignmentStatus.assigned,
    )

    shift: Mapped["ScheduleShift"] = relationship("ScheduleShift", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("shift_id", "membership_id", name="uq_sched_assignment"),
        Index("ix_sched_assignment_membership", "membership_id"),
    )


class RuleType(str, enum.Enum):
    coverage = "coverage"        # min/max staff counts
    availability = "availability"  # days off, preferred hours
    fairness = "fairness"        # distribute hours evenly
    constraint = "constraint"    # generic / catch-all


class ScheduleRule(UUIDMixin, TimestampMixin, Base):
    """A natural-language scheduling rule, optionally parsed into structured JSON."""
    __tablename__ = "schedule_rules"

    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    rule_type: Mapped[RuleType] = mapped_column(
        Enum(RuleType, name="schedule_rule_type"), nullable=False, default=RuleType.constraint
    )
    parsed_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    __table_args__ = (
        Index("ix_schedule_rules_biz_active", "business_id", "is_active"),
    )
