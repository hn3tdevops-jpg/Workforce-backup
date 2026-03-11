"""agent_run_nullable_agent_id

Revision ID: 78f6a32a1e9c
Revises: b2c72fca8a05
Create Date: 2026-02-22 11:18:55.411992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78f6a32a1e9c'
down_revision: Union[str, None] = 'b2c72fca8a05'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('agent_runs', schema=None) as batch_op:
        batch_op.alter_column('agent_id', existing_type=sa.String(36), nullable=True)
        batch_op.alter_column('correlation_id', existing_type=sa.String(36), type_=sa.String(100), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('agent_runs', schema=None) as batch_op:
        batch_op.alter_column('agent_id', existing_type=sa.String(36), nullable=False)
        batch_op.alter_column('correlation_id', existing_type=sa.String(100), type_=sa.String(36), nullable=True)
