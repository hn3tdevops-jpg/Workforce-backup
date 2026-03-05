"""create initial tables

Revision ID: 0001
Revises: 
Create Date: 2026-03-02
"""
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'roles',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('business_id', sa.String(), nullable=False),
        sa.Column('scope_type', sa.String(), nullable=False),
        sa.Column('location_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
    )
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('key', sa.String(), nullable=False),
    )
    op.create_table(
        'role_permissions',
        sa.Column('role_id', sa.String(), sa.ForeignKey('roles.id')),
        sa.Column('permission_id', sa.String(), sa.ForeignKey('permissions.id')),
    )

def downgrade():
    op.drop_table('role_permissions')
    op.drop_table('permissions')
    op.drop_table('roles')
