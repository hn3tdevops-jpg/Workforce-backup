"""
Revision ID: merge_0002_20260420_proper
Revises: 15d9d2ac7871
Create Date: 2026-04-25
"""

# revision identifiers, used by Alembic.
revision = 'merge_0002_20260420_proper'
down_revision = ('15d9d2ac7871',)
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Merge migration (no-op). Aligns package alembic with top-level revision state.
    pass


def downgrade():
    # No-op downgrade
    pass
