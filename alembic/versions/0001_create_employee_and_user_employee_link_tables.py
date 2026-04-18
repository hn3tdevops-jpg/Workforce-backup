"""create employee and user_employee_link tables

Revision ID: 0001_create_employee_and_user_employee_link_tables
Revises: 
Create Date: 2026-04-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_create_employee_and_user_employee_link_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'employee_profiles',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('business_id', sa.String(length=36), nullable=False),
        sa.Column('location_id', sa.String(length=36), nullable=True),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=120), nullable=True),
        sa.Column('last_name', sa.String(length=120), nullable=True),
        sa.Column('email_work', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        'user_employee_links',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('employee_id', sa.String(length=36), nullable=False),
        sa.Column('business_id', sa.String(length=36), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('created_by', sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('user_employee_links')
    op.drop_table('employee_profiles')
