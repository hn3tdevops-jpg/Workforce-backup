"""
Revision ID: merge_0002_20260420_proper
Revises: 0002_normalize_uuid_columns, 20260420_consolidate_models
Create Date: 2026-04-24
"""

# revision identifiers, used by Alembic.
revision = 'merge_0002_20260420_proper'
down_revision = ('0002_normalize_uuid_columns', '20260420_consolidate_models')
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    # Merge migration (no-op). This merges the two divergent heads into one.
    pass


def downgrade():
    # No-op downgrade
    pass
