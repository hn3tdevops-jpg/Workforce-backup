"""add tenancy tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-05
"""

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'businesses',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('plan', sa.String(), nullable=False, server_default='free'),
        sa.Column('settings_json', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'locations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('business_id', sa.String(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.String(), sa.ForeignKey('locations.id', ondelete='CASCADE'), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('timezone', sa.String(), nullable=False, server_default='UTC'),
        sa.Column('settings_json', sa.Text(), nullable=True),
    )
    op.create_index('ix_locations_business', 'locations', ['business_id'])

    op.create_table(
        'memberships',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('business_id', sa.String(), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('primary_location_id', sa.String(), sa.ForeignKey('locations.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
    )
    op.create_unique_constraint('uq_membership_user_business', 'memberships', ['user_id', 'business_id'])
    op.create_index('ix_membership_business_status', 'memberships', ['business_id', 'status'])


def downgrade():
    op.drop_index('ix_membership_business_status', table_name='memberships')
    op.drop_constraint('uq_membership_user_business', 'memberships', type_='unique')
    op.drop_table('memberships')
    op.drop_index('ix_locations_business', table_name='locations')
    op.drop_table('locations')
    op.drop_table('businesses')
