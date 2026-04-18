"""normalize uuid columns to consistent String(36)

Revision ID: 0002_normalize_uuid_columns
Revises: 0001_initial
Create Date: 2026-04-18 14:24:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_normalize_uuid_columns'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # For SQLite, use batch_alter_table which will recreate tables preserving data.
    # Normalize common UUID columns to String(36) so SQLAlchemy comparisons are stable.

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('business_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=True)

    with op.batch_alter_table('tenants') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)

    with op.batch_alter_table('businesses') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('tenant_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=True)

    with op.batch_alter_table('locations') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('business_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)

    with op.batch_alter_table('memberships') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('user_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('business_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)

    with op.batch_alter_table('roles') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('business_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)

    with op.batch_alter_table('scoped_role_assignments') as batch_op:
        batch_op.alter_column('id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('membership_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('role_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=False)
        batch_op.alter_column('location_id', existing_type=sa.TEXT(), type_=sa.String(length=36), existing_nullable=True)


def downgrade():
    # Revert type changes back to TEXT
    with op.batch_alter_table('scoped_role_assignments') as batch_op:
        batch_op.alter_column('location_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=True)
        batch_op.alter_column('role_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('membership_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('roles') as batch_op:
        batch_op.alter_column('business_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('memberships') as batch_op:
        batch_op.alter_column('business_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('user_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('locations') as batch_op:
        batch_op.alter_column('business_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('businesses') as batch_op:
        batch_op.alter_column('tenant_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=True)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('tenants') as batch_op:
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)

    with op.batch_alter_table('users') as batch_op:
        batch_op.alter_column('business_id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=True)
        batch_op.alter_column('id', existing_type=sa.String(length=36), type_=sa.TEXT(), existing_nullable=False)
