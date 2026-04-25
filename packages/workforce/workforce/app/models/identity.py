"""
Identity, tenancy, RBAC, agents, and audit models for the control plane system.
These supplement (not replace) the existing scheduling models.
"""
import enum

from sqlalchemy import (
    Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from packages.workforce.workforce.app.models.base import Base, TimestampMixin, UUIDMixin
# Runtime import required so SQLAlchemy can resolve relationship("Location")
# on MembershipLocationRole during mapper configuration.
from packages.workforce.workforce.app.models.business import Location  # noqa: F401


# ── Enums ────────────────────────────────────────────────────────────────────

class UserStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"
    invited = "invited"


class MembershipStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    invited = "invited"
    removed = "removed"


class ActorType(str, enum.Enum):
    user = "user"
    agent = "agent"
    system = "system"


class AgentType(str, enum.Enum):
    integration = "integration"
    ai = "ai"
    webhook = "webhook"
    service = "service"


class AgentStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"


class AgentRunStatus(str, enum.Enum):
    running = "running"
    success = "success"
    failed = "failed"
    retrying = "retrying"


# ── Identity ─────────────────────────────────────────────────────────────────

class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status"), default=UserStatus.active, nullable=False
    )

    # Backcompat property for older code that expects a boolean is_active field.
    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.active

    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bio: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    memberships: Mapped[list["Membership"]] = relationship("Membership", back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship("RefreshToken", back_populates="user")


class RefreshToken(UUIDMixin, Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")


# ── Tenancy ───────────────────────────────────────────────────────────────────

class Membership(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "memberships"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    business_id: Mapped[str] = mapped_column(String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    primary_location_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("locations.id"), nullable=True)
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status"),
        default=MembershipStatus.active, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    worker_profile: Mapped["WorkerProfile | None"] = relationship("WorkerProfile", back_populates="membership", uselist=False)
    membership_roles: Mapped[list["MembershipRole"]] = relationship("MembershipRole", back_populates="membership")
    location_roles: Mapped[list["MembershipLocationRole"]] = relationship("MembershipLocationRole", back_populates="membership")
    availability_blocks: Mapped[list["WorkerAvailability"]] = relationship("WorkerAvailability", back_populates="membership")

    __table_args__ = (
        UniqueConstraint("user_id", "business_id", name="uq_membership_user_business"),
        Index("ix_membership_business_status", "business_id", "status"),
    )


class WorkerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "worker_profiles"

    membership_id: Mapped[str] = mapped_column(String(36), ForeignKey("memberships.id", ondelete="CASCADE"), unique=True, nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    pay_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    hire_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date YYYY-MM-DD
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Worker profiling for eligibility matching
    qualified_roles: Mapped[str | None] = mapped_column(Text, nullable=True)   # JSON array e.g. ["Barista","Cashier"]
    skills: Mapped[str | None] = mapped_column(Text, nullable=True)            # JSON array e.g. ["Latte Art"]
    certifications: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON array e.g. ["Food Handler"]
    max_weekly_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    membership: Mapped["Membership"] = relationship("Membership", back_populates="worker_profile")


# ── RBAC ──────────────────────────────────────────────────────────────────────

class BizRole(UUIDMixin, TimestampMixin, Base):
    """Business-scoped role (distinct from the scheduling Role model)."""
    __tablename__ = "biz_roles"

    business_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True
    )  # NULL = system template (superadmin-defined)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_system_template: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # BUSINESS = applies business-wide; LOCATION = intended for per-location assignment
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False, default="BUSINESS")
    # When scope_type='LOCATION' and not a system template, optionally pin to a specific location
    location_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )
    # Higher priority = preferred display role when a user holds multiple roles
    priority: Mapped[int | None] = mapped_column(Integer, nullable=True)

    permissions: Mapped[list["BizRolePermission"]] = relationship("BizRolePermission", back_populates="role")
    membership_roles: Mapped[list["MembershipRole"]] = relationship("MembershipRole", back_populates="role")

    __table_args__ = (
        UniqueConstraint("business_id", "name", name="uq_bizrole_business_name"),
    )


class Permission(UUIDMixin, Base):
    """Global permission registry. key format: 'module:action'."""
    __tablename__ = "permissions"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)


class BizRolePermission(Base):
    __tablename__ = "biz_role_permissions"

    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("biz_roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id: Mapped[str] = mapped_column(String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)

    role: Mapped["BizRole"] = relationship("BizRole", back_populates="permissions")
    permission: Mapped["Permission"] = relationship("Permission")


class MembershipRole(Base):
    __tablename__ = "membership_roles"

    membership_id: Mapped[str] = mapped_column(String(36), ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("biz_roles.id", ondelete="CASCADE"), primary_key=True)
    job_title_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    membership: Mapped["Membership"] = relationship("Membership", back_populates="membership_roles")
    role: Mapped["BizRole"] = relationship("BizRole", back_populates="membership_roles")


class MembershipLocationRole(Base):
    """Per-location role override — grants a member extra (or different) roles at a specific location."""
    __tablename__ = "membership_location_roles"

    membership_id: Mapped[str] = mapped_column(String(36), ForeignKey("memberships.id", ondelete="CASCADE"), primary_key=True)
    location_id: Mapped[str] = mapped_column(String(36), ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("biz_roles.id", ondelete="CASCADE"), primary_key=True)
    # Display label for profile/job title; falls back to role.name if not set
    job_title_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    membership: Mapped["Membership"] = relationship("Membership", back_populates="location_roles")
    location: Mapped["Location"] = relationship("Location")
    role: Mapped["BizRole"] = relationship("BizRole")


class WorkerAvailability(UUIDMixin, TimestampMixin, Base):
    """Weekly recurring availability block owned by a v1 Membership."""
    __tablename__ = "worker_availability"

    membership_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(nullable=False)  # 0=Mon … 6=Sun
    start_hour: Mapped[float] = mapped_column(nullable=False)  # e.g. 9.0 = 09:00
    end_hour: Mapped[float] = mapped_column(nullable=False)    # e.g. 17.5 = 17:30

    membership: Mapped["Membership"] = relationship("Membership", back_populates="availability_blocks")

    __table_args__ = (
        CheckConstraint("end_hour > start_hour", name="ck_worker_avail_end_after_start"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_worker_avail_day"),
    )


# ── Agents ────────────────────────────────────────────────────────────────────

class Agent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agents"

    business_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True
    )  # NULL = platform-level agent
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[AgentType] = mapped_column(
        Enum(AgentType, name="agent_type"), nullable=False, default=AgentType.integration
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus, name="agent_status"), nullable=False, default=AgentStatus.active
    )

    credentials: Mapped[list["AgentCredential"]] = relationship("AgentCredential", back_populates="agent")
    runs: Mapped[list["AgentRun"]] = relationship("AgentRun", back_populates="agent")


class AgentCredential(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "agent_credentials"

    agent_id: Mapped[str] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)  # first 8 chars for lookup/display
    scopes_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    expires_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="credentials")


class AgentRun(UUIDMixin, Base):
    __tablename__ = "agent_runs"

    agent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True)
    started_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus, name="agent_run_status"), nullable=False, default=AgentRunStatus.running
    )
    logs_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="runs")


# ── Audit ─────────────────────────────────────────────────────────────────────

class AuditEvent(UUIDMixin, Base):
    __tablename__ = "audit_events"

    business_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    actor_type: Mapped[ActorType] = mapped_column(
        Enum(ActorType, name="actor_type"), nullable=False
    )
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    diff_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    correlation_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("ix_audit_events_business_created", "business_id", "created_at"),
    )
