from __future__ import annotations

import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.app.models.employee import Employee

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from apps.api.app.models.base import Base, TimestampMixin, UUIDMixin


class AvailabilityStatus(str, enum.Enum):
    preferred = "preferred"
    available = "available"
    unavailable = "unavailable"


class ShiftStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    cancelled = "cancelled"


class AssignmentStatus(str, enum.Enum):
    offered = "offered"
    assigned = "assigned"
    checked_in = "checked_in"
    no_show = "no_show"
    cancelled = "cancelled"


class AvailabilityBlock(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "availability_blocks"

    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    start_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[AvailabilityStatus] = mapped_column(
        Enum(AvailabilityStatus, name="availability_status"),
        nullable=False,
        default=AvailabilityStatus.available,
    )

    employee: Mapped["Employee"] = relationship("Employee", back_populates="availability_blocks")

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_availability_end_after_start"),
        Index("ix_availability_employee_window", "employee_id", "start_ts", "end_ts"),
    )


class Shift(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "shifts"

    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    start_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    end_ts: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    needed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[ShiftStatus] = mapped_column(
        Enum(ShiftStatus, name="shift_status"),
        nullable=False,
        default=ShiftStatus.draft,
    )

    assignments: Mapped[list["ShiftAssignment"]] = relationship(
        "ShiftAssignment", back_populates="shift"
    )

    __table_args__ = (
        CheckConstraint("end_ts > start_ts", name="ck_shift_end_after_start"),
        CheckConstraint("needed_count >= 1", name="ck_shift_needed_count"),
        Index("ix_shifts_role_window", "role_id", "start_ts", "end_ts"),
    )


class ShiftAssignment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "shift_assignments"

    shift_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("shifts.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[AssignmentStatus] = mapped_column(
        Enum(AssignmentStatus, name="assignment_status"),
        nullable=False,
        default=AssignmentStatus.offered,
    )

    shift: Mapped["Shift"] = relationship("Shift", back_populates="assignments")

    __table_args__ = (
        UniqueConstraint("shift_id", "employee_id", name="uq_shift_assignment"),
    )
