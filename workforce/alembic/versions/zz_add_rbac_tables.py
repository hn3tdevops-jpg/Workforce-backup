"""
Create RBAC core tables: permissions, roles, role_permissions, user_role_assignments

Revision ID: zz_add_rbac_tables
Revises: b7c2e4f1a9d3
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa
from typing import Union

revision: str = 'zz_add_rbac_tables'
down_revision: Union[str, None] = 'b7c2e4f1a9d3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('key', sa.String(200), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'roles',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('business_id', sa.String(36), nullable=True),
        sa.Column('scope_type', sa.String(20), nullable=False, server_default='BUSINESS'),
        sa.Column('location_id', sa.String(36), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('permission_id', sa.String(36), nullable=False),
        sa.PrimaryKeyConstraint('role_id', 'permission_id')
    )

    op.create_table(
        'user_role_assignments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('business_id', sa.String(36), nullable=False),
        sa.Column('scope_type', sa.String(20), nullable=False),
        sa.Column('location_id', sa.String(36), nullable=True),
        sa.Column('role_id', sa.String(36), nullable=False),
        sa.Column('job_title_label', sa.String(100), nullable=True),
        sa.Column('created_by_user_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('user_role_assignments')
    op.drop_table('role_permissions')
    op.drop_table('roles')
    op.drop_table('permissions')
