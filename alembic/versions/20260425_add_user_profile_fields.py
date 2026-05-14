"""
Add user profile fields to top-level migrations so dev DB matches package models.

Revision ID: 20260425_add_user_profile_fields
Revises: merge_0002_20260420_proper
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260425_add_user_profile_fields'
down_revision = ('merge_0002_20260420_proper',)
branch_labels = None
depends_on = None


def upgrade():
    # Add columns to users to match packages.workforce models
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('phone', sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column('is_superadmin', sa.Boolean(), nullable=False, server_default=sa.text('0')))
        batch_op.add_column(sa.Column('status', sa.Enum('active','suspended','deleted','invited', name='user_status'), nullable=False, server_default='active'))
        batch_op.add_column(sa.Column('first_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('emergency_contact_name', sa.String(length=150), nullable=True))
        batch_op.add_column(sa.Column('emergency_contact_phone', sa.String(length=30), nullable=True))
        # Ensure updated_at exists
        try:
            batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        except Exception:
            pass

    # Add worker_profiles fields if present
    try:
        with op.batch_alter_table('worker_profiles', schema=None) as batch_op:
            batch_op.add_column(sa.Column('hire_date', sa.String(length=10), nullable=True))
            batch_op.add_column(sa.Column('notes', sa.String(length=1000), nullable=True))
    except Exception:
        # table might not exist in all deployments; tolerate
        pass


def downgrade():
    try:
        with op.batch_alter_table('worker_profiles', schema=None) as batch_op:
            batch_op.drop_column('notes')
            batch_op.drop_column('hire_date')
    except Exception:
        pass

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('emergency_contact_phone')
        batch_op.drop_column('emergency_contact_name')
        batch_op.drop_column('bio')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')
        try:
            batch_op.drop_column('updated_at')
        except Exception:
            pass
        batch_op.drop_column('status')
        batch_op.drop_column('is_superadmin')
        batch_op.drop_column('phone')
