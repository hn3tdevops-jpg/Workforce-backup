"""
Alembic stub: consolidate models to canonical packages.workforce

Revision ID: 20260420_consolidate_models
Revises: <set to current alembic head>
Create Date: 2026-04-20
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260420_consolidate_models'
down_revision = None  # TODO: set to current head
branch_labels = None
depends_on = None


def upgrade():
    """
    NOTE: This file is a template. Replace placeholders with explicit
    non-destructive upgrade steps. Typical pattern:
      - Add new columns/tables required by canonical models (nullable)
      - Backfill data from legacy tables/columns
      - Update application to write to canonical columns
      - Run verification
      - Drop legacy columns/tables in a follow-up revision

    For SQLite, use op.batch_alter_table(...) when altering constraints or column types.
    """
    # Example (commented):
    # with op.batch_alter_table('users') as batch_op:
    #     batch_op.add_column(sa.Column('new_uuid', sa.String(length=36), nullable=True))
    pass


def downgrade():
    # Reverse operations where feasible. Prefer writing explicit reverse steps.
    pass
