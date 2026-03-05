"""per-location RBAC: scope_type/location_id/priority on biz_roles; job_title_label/created_by on assignments

Revision ID: b7c2e4f1a9d3
Revises: a1b2c3d4e5f6
Create Date: 2026-02-22

"""
from typing import Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b7c2e4f1a9d3'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── biz_roles: scope_type, location_id, priority ─────────────────────────
    with op.batch_alter_table('biz_roles') as batch_op:
        batch_op.add_column(sa.Column('scope_type', sa.String(20), nullable=False, server_default='BUSINESS'))
        batch_op.add_column(sa.Column('location_id', sa.String(36), nullable=True))
        batch_op.add_column(sa.Column('priority', sa.Integer(), nullable=True))

    # ── membership_location_roles: job_title_label, created_by_user_id ───────
    with op.batch_alter_table('membership_location_roles') as batch_op:
        batch_op.add_column(sa.Column('job_title_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('created_by_user_id', sa.String(36), nullable=True))

    # ── membership_roles: job_title_label, created_by_user_id ────────────────
    with op.batch_alter_table('membership_roles') as batch_op:
        batch_op.add_column(sa.Column('job_title_label', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('created_by_user_id', sa.String(36), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('membership_roles') as batch_op:
        batch_op.drop_column('created_by_user_id')
        batch_op.drop_column('job_title_label')

    with op.batch_alter_table('membership_location_roles') as batch_op:
        batch_op.drop_column('created_by_user_id')
        batch_op.drop_column('job_title_label')

    with op.batch_alter_table('biz_roles') as batch_op:
        batch_op.drop_column('priority')
        batch_op.drop_column('location_id')
        batch_op.drop_column('scope_type')
