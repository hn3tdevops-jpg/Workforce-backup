"""Platform access control foundation: tenants, memberships, roles, permissions,
role_permissions, scoped_role_assignments, and tenant linkage for businesses.

Revision ID: 0003_platform_access_control
Revises: 0002_hospitable_property_ops
Create Date: 2026-03-18
"""

from __future__ import annotations

import uuid

from alembic import op
import sqlalchemy as sa


revision = "0003_platform_access_control"
down_revision = "0002_hospitable_property_ops"
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def _uuid_type() -> sa.types.TypeEngine:
    if _is_sqlite():
        return sa.String(36)
    from sqlalchemy.dialects.postgresql import UUID
    return UUID(as_uuid=False)


def _json_type() -> sa.types.TypeEngine:
    if _is_sqlite():
        return sa.JSON()
    from sqlalchemy.dialects.postgresql import JSONB
    return JSONB()


def upgrade() -> None:
    uuid_type = _uuid_type()

    # ------------------------------------------------------------------ #
    # tenants
    # ------------------------------------------------------------------ #
    op.create_table(
        "tenants",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=True),
        sa.Column("settings_json", _json_type(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # ------------------------------------------------------------------ #
    # businesses.tenant_id
    # Keep nullable in this migration for safest rollout/backfill.
    # Tighten later after verification.
    # ------------------------------------------------------------------ #
    with op.batch_alter_table("businesses", recreate="always") as batch_op:
        batch_op.add_column(sa.Column("tenant_id", uuid_type, nullable=True))
        batch_op.create_foreign_key(
            "fk_businesses_tenant_id_tenants",
            "tenants",
            ["tenant_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    op.create_index("ix_businesses_tenant_id", "businesses", ["tenant_id"], unique=False)

    # ------------------------------------------------------------------ #
    # memberships
    # user <-> business membership, replacing direct ownership logic later
    # ------------------------------------------------------------------ #
    op.create_table(
        "memberships",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "user_id",
            uuid_type,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "business_id",
            uuid_type,
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("is_owner", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("user_id", "business_id", name="uq_memberships_user_business"),
    )
    op.create_index("ix_memberships_user_id", "memberships", ["user_id"], unique=False)
    op.create_index("ix_memberships_business_id", "memberships", ["business_id"], unique=False)

    # ------------------------------------------------------------------ #
    # roles
    # business-scoped for now
    # ------------------------------------------------------------------ #
    op.create_table(
        "roles",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "business_id",
            uuid_type,
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_system", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("business_id", "name", name="uq_roles_business_name"),
    )
    op.create_index("ix_roles_business_id", "roles", ["business_id"], unique=False)

    # ------------------------------------------------------------------ #
    # permissions
    # global permission catalog
    # ------------------------------------------------------------------ #
    op.create_table(
        "permissions",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("code", sa.String(120), nullable=False),
        sa.Column("resource", sa.String(120), nullable=False),
        sa.Column("action", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.UniqueConstraint("code", name="uq_permissions_code"),
    )

    # ------------------------------------------------------------------ #
    # role_permissions
    # ------------------------------------------------------------------ #
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            uuid_type,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "permission_id",
            uuid_type,
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
    )

    # ------------------------------------------------------------------ #
    # scoped_role_assignments
    # location_id NULL => business-wide assignment
    # location_id set  => location-scoped assignment
    # ------------------------------------------------------------------ #
    op.create_table(
        "scoped_role_assignments",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column(
            "membership_id",
            uuid_type,
            sa.ForeignKey("memberships.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role_id",
            uuid_type,
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            uuid_type,
            sa.ForeignKey("locations.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_scoped_role_assignments_membership_id",
        "scoped_role_assignments",
        ["membership_id"],
        unique=False,
    )
    op.create_index(
        "ix_scoped_role_assignments_role_id",
        "scoped_role_assignments",
        ["role_id"],
        unique=False,
    )
    op.create_index(
        "ix_scoped_role_assignments_location_id",
        "scoped_role_assignments",
        ["location_id"],
        unique=False,
    )

    # ------------------------------------------------------------------ #
    # Data backfill
    # - one tenant per existing business
    # - one membership per existing user.business_id
    # ------------------------------------------------------------------ #
    conn = op.get_bind()

    business_rows = list(conn.execute(sa.text("SELECT id, name FROM businesses")))
    for business_id, business_name in business_rows:
        tenant_id = str(uuid.uuid4())
        slug = (
            business_name.lower()
            .replace("&", " and ")
            .replace("/", " ")
            .replace("\\", " ")
            .replace(".", " ")
            .replace(",", " ")
            .replace("'", "")
            .strip()
        )
        slug = "-".join(part for part in slug.split() if part) or f"tenant-{tenant_id[:8]}"

        conn.execute(
            sa.text(
                """
                INSERT INTO tenants (id, name, slug, is_active)
                VALUES (:id, :name, :slug, :is_active)
                """
            ),
            {
                "id": tenant_id,
                "name": business_name,
                "slug": slug,
                "is_active": True,
            },
        )

        conn.execute(
            sa.text(
                """
                UPDATE businesses
                SET tenant_id = :tenant_id
                WHERE id = :business_id
                """
            ),
            {
                "tenant_id": tenant_id,
                "business_id": business_id,
            },
        )

    membership_rows = list(
        conn.execute(
            sa.text(
                """
                SELECT id, business_id
                FROM users
                WHERE business_id IS NOT NULL
                """
            )
        )
    )
    for user_id, business_id in membership_rows:
        membership_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                """
                INSERT INTO memberships (id, user_id, business_id, status, is_owner)
                VALUES (:id, :user_id, :business_id, :status, :is_owner)
                """
            ),
            {
                "id": membership_id,
                "user_id": user_id,
                "business_id": business_id,
                "status": "active",
                "is_owner": False,
            },
        )

    # ------------------------------------------------------------------ #
    # Seed a minimal global permission catalog
    # ------------------------------------------------------------------ #
    permission_rows = [
        ("users.read", "users", "read", "Read users"),
        ("users.manage", "users", "manage", "Manage users"),
        ("businesses.read", "businesses", "read", "Read businesses"),
        ("businesses.manage", "businesses", "manage", "Manage businesses"),
        ("locations.read", "locations", "read", "Read locations"),
        ("locations.manage", "locations", "manage", "Manage locations"),
        ("schedule.read", "schedule", "read", "Read schedules"),
        ("schedule.manage", "schedule", "manage", "Manage schedules"),
        ("time.read", "time", "read", "Read time entries"),
        ("time.manage", "time", "manage", "Manage time entries"),
        ("inventory.read", "inventory", "read", "Read inventory"),
        ("inventory.manage", "inventory", "manage", "Manage inventory"),
        ("hk.rooms.read", "hk.rooms", "read", "Read housekeeping rooms"),
        ("hk.tasks.manage", "hk.tasks", "manage", "Manage housekeeping tasks"),
    ]
    for code, resource, action, description in permission_rows:
        conn.execute(
            sa.text(
                """
                INSERT INTO permissions (id, code, resource, action, description)
                VALUES (:id, :code, :resource, :action, :description)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "resource": resource,
                "action": action,
                "description": description,
            },
        )


def downgrade() -> None:
    op.drop_index("ix_scoped_role_assignments_location_id", table_name="scoped_role_assignments")
    op.drop_index("ix_scoped_role_assignments_role_id", table_name="scoped_role_assignments")
    op.drop_index("ix_scoped_role_assignments_membership_id", table_name="scoped_role_assignments")
    op.drop_table("scoped_role_assignments")

    op.drop_table("role_permissions")

    op.drop_table("permissions")

    op.drop_index("ix_roles_business_id", table_name="roles")
    op.drop_table("roles")

    op.drop_index("ix_memberships_business_id", table_name="memberships")
    op.drop_index("ix_memberships_user_id", table_name="memberships")
    op.drop_table("memberships")

    op.drop_index("ix_businesses_tenant_id", table_name="businesses")

    with op.batch_alter_table("businesses", recreate="always") as batch_op:
        batch_op.drop_constraint("fk_businesses_tenant_id_tenants", type_="foreignkey")
        batch_op.drop_column("tenant_id")

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")