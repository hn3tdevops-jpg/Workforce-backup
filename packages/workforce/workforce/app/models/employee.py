from __future__ import annotations

import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.api.app.models.scheduling import AvailabilityBlock

from sqlalchemy import (
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.workforce.workforce.app.models.base import Base, TimestampMixin, UUIDMixin


class EmploymentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    terminated = "terminated"


class Employee(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    employments: Mapped[list["Employment"]] = relationship("Employment", back_populates="employee")
    availability_blocks: Mapped[list["AvailabilityBlock"]] = relationship(
        "AvailabilityBlock", back_populates="employee"
    )
# Backwards compatibility: some parts of this repository reference EmployeeProfile
# (a local apps.api.app model). Provide an alias so imports like
# `from apps.api.app.models.employee import EmployeeProfile` succeed when the
# packages.workforce model is discovered first.
EmployeeProfile = Employee


class Employment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employments"

    business_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False
    )
    employee_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus, name="employment_status"), nullable=False, default=EmploymentStatus.active
    )
    hire_date: Mapped[str | None] = mapped_column(Date, nullable=True)

    employee: Mapped["Employee"] = relationship("Employee", back_populates="employments")
    roles: Mapped[list["EmployeeRole"]] = relationship("EmployeeRole", back_populates="employment")

    __table_args__ = (
        UniqueConstraint("business_id", "employee_id", name="uq_employment_business_employee"),
        Index("ix_employments_business_employee_status", "business_id", "employee_id", "status"),
    )


class Role(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class EmployeeRole(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employee_roles"

    employment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employments.id", ondelete="CASCADE"), nullable=False
    )
    role_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    proficiency: Mapped[int] = mapped_column(Integer, nullable=False, default=3)

    employment: Mapped["Employment"] = relationship("Employment", back_populates="roles")

    __table_args__ = (
        UniqueConstraint("employment_id", "role_id", name="uq_employee_role"),
        CheckConstraint("proficiency >= 1 AND proficiency <= 5", name="ck_proficiency_range"),
    )
