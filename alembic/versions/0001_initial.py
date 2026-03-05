"""Initial migration: create businesses, locations, users tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def _is_sqlite() -> bool:
    bind = op.get_bind()
    return bind.dialect.name == "sqlite"


def upgrade() -> None:
    if _is_sqlite():
        uuid_type = sa.String(36)
        json_type = sa.JSON()
    else:
        from sqlalchemy.dialects.postgresql import UUID, JSONB
        uuid_type = UUID(as_uuid=False)
        json_type = JSONB()

    op.create_table(
        "businesses",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("settings_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "locations",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("business_id", uuid_type, sa.ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("settings_json", json_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", uuid_type, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column("business_id", uuid_type, sa.ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
    op.drop_table("locations")
    op.drop_table("businesses")
