import os
from apps.api.app.core.imports import record_model_import

# Diagnostic record
try:
    record_model_import(__name__)
except Exception:
    pass

# Prefer canonical identity models when available; fall back to local definitions where necessary.
if not os.environ.get('SKIP_WORKFORCE_MODELS'):
    try:
        from packages.workforce.workforce.app.models.identity import (
            Membership as CanonicalMembership,
            BizRole as CanonicalRole,
            Permission as CanonicalPermission,
            BizRolePermission as CanonicalRolePermission,
            MembershipRole as CanonicalMembershipRole,
            MembershipLocationRole as CanonicalMembershipLocationRole,
        )
        # ScopedRoleAssignment/table may be local-only; attempt import but tolerate failure.
        try:
            from packages.workforce.workforce.app.models.identity import ScopedRoleAssignment as CanonicalScopedRoleAssignment
        except Exception:
            CanonicalScopedRoleAssignment = None

        # Alias canonical names to local exports where possible.
        Membership = CanonicalMembership
        Role = CanonicalRole
        Permission = CanonicalPermission
        RolePermission = CanonicalRolePermission
        MembershipRole = CanonicalMembershipRole
        MembershipLocationRole = CanonicalMembershipLocationRole

        # Prepare __all__ for the canonical exports; ScopedRoleAssignment may be added below.
        __all__ = [
            "Membership",
            "Role",
            "Permission",
            "RolePermission",
            "MembershipRole",
            "MembershipLocationRole",
        ]
        if CanonicalScopedRoleAssignment is not None:
            ScopedRoleAssignment = CanonicalScopedRoleAssignment
            __all__.append("ScopedRoleAssignment")

        # Canonical import succeeded; only provide local fallbacks for missing pieces.
        _IMPORTED_CANONICAL = True
    except Exception:
        _IMPORTED_CANONICAL = False
else:
    _IMPORTED_CANONICAL = False

if not _IMPORTED_CANONICAL:
    import uuid
    from datetime import datetime

    from sqlalchemy import Boolean, ForeignKey, Index, PrimaryKeyConstraint, String, Text, UniqueConstraint, func, text
    from sqlalchemy.orm import Mapped, mapped_column, relationship

    from apps.api.app.models.base import Base


    def _sqlite_uuid_server_default():
        return text(
            "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || "
            "substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || "
            "substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))"
        )


    class Membership(Base):
        __tablename__ = "memberships"
        __table_args__ = (
            UniqueConstraint("user_id", "business_id", name="uq_memberships_user_business"),
            Index("ix_memberships_user_id", "user_id"),
            Index("ix_memberships_business_id", "business_id"),
        )

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            server_default=_sqlite_uuid_server_default(),
        )
        user_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
        )
        business_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False,
        )
        status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", server_default="active")
        is_owner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
        created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

        user = relationship("User")
        business = relationship("Business")


    class Role(Base):
        __tablename__ = "roles"
        __table_args__ = (
            UniqueConstraint("business_id", "name", name="uq_roles_business_name"),
            Index("ix_roles_business_id", "business_id"),
        )

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            server_default=_sqlite_uuid_server_default(),
        )
        business_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        )
        name: Mapped[str] = mapped_column(String(120), nullable=False)
        description: Mapped[str | None] = mapped_column(Text, nullable=True)
        is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
        created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

        business = relationship("Business")


    class Permission(Base):
        __tablename__ = "permissions"
        __table_args__ = (
            UniqueConstraint("code", name="uq_permissions_code"),
        )

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            server_default=_sqlite_uuid_server_default(),
        )
        code: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
        resource: Mapped[str] = mapped_column(String(120), nullable=False)
        action: Mapped[str] = mapped_column(String(120), nullable=False)
        description: Mapped[str | None] = mapped_column(Text, nullable=True)


    class RolePermission(Base):
        __tablename__ = "role_permissions"
        __table_args__ = (
            PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
        )

        role_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("roles.id", ondelete="CASCADE"), nullable=False,
        )
        permission_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False,
        )

        role = relationship("Role")
        permission = relationship("Permission")


    class ScopedRoleAssignment(Base):
        __tablename__ = "scoped_role_assignments"
        __table_args__ = (
            Index("ix_scoped_role_assignments_membership_id", "membership_id"),
            Index("ix_scoped_role_assignments_role_id", "role_id"),
            Index("ix_scoped_role_assignments_location_id", "location_id"),
        )

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            server_default=_sqlite_uuid_server_default(),
        )
        membership_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False,
        )
        role_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("roles.id", ondelete="CASCADE"), nullable=False,
        )
        location_id: Mapped[uuid.UUID | None] = mapped_column(
            ForeignKey("locations.id", ondelete="CASCADE"), nullable=True,
        )
        created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

        membership = relationship("Membership")
        role = relationship("Role")
        location = relationship("Location")

    __all__ = [
        "Membership",
        "Role",
        "Permission",
        "RolePermission",
        "ScopedRoleAssignment",
    ]

# If canonical package is present but does not provide ScopedRoleAssignment,
# define a minimal local ScopedRoleAssignment that reuses the canonical
# Membership/Role/Location classes where available.
if 'ScopedRoleAssignment' not in globals():
    import uuid
    from datetime import datetime

    from sqlalchemy import Boolean, ForeignKey, Index, String, Text, func, text
    from sqlalchemy.orm import Mapped, mapped_column, relationship
    from apps.api.app.models.base import Base


    def _sqlite_uuid_server_default():
        return text(
            "(lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || "
            "substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || "
            "substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6))))"
        )


    class ScopedRoleAssignment(Base):
        __tablename__ = "scoped_role_assignments"
        __table_args__ = (
            Index("ix_scoped_role_assignments_membership_id", "membership_id"),
            Index("ix_scoped_role_assignments_role_id", "role_id"),
            Index("ix_scoped_role_assignments_location_id", "location_id"),
        )

        id: Mapped[uuid.UUID] = mapped_column(
            primary_key=True,
            default=uuid.uuid4,
            server_default=_sqlite_uuid_server_default(),
        )
        membership_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("memberships.id", ondelete="CASCADE"), nullable=False,
        )
        role_id: Mapped[uuid.UUID] = mapped_column(
            ForeignKey("roles.id", ondelete="CASCADE"), nullable=False,
        )
        location_id: Mapped[uuid.UUID | None] = mapped_column(
            ForeignKey("locations.id", ondelete="CASCADE"), nullable=True,
        )
        created_at: Mapped[datetime | None] = mapped_column(server_default=func.now())

        membership = relationship("Membership")
        role = relationship("Role")
        location = relationship("Location")

    __all__ = globals().get("__all__", []) + ["ScopedRoleAssignment"]
