"""add worker_availability table

Revision ID: a1b2c3d4e5f6
Revises: cbd29a293ca6
Create Date: 2026-02-20

"""
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'cbd29a293ca6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'worker_availability',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('membership_id', sa.String(36), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_hour', sa.Float(), nullable=False),
        sa.Column('end_hour', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('end_hour > start_hour', name='ck_worker_avail_end_after_start'),
        sa.CheckConstraint('day_of_week >= 0 AND day_of_week <= 6', name='ck_worker_avail_day'),
        sa.ForeignKeyConstraint(['membership_id'], ['memberships.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('worker_availability') as batch_op:
        batch_op.create_index('ix_worker_availability_membership_id', ['membership_id'])


def downgrade() -> None:
    op.drop_table('worker_availability')
