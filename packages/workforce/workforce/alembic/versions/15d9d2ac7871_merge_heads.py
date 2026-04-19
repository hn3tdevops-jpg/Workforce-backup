"""merge heads

Revision ID: 15d9d2ac7871
Revises: 8b9724120087, f1e2d3c4b5a6
Create Date: 2026-03-12 19:56:03.679692

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '15d9d2ac7871'
down_revision: Union[str, None] = ('8b9724120087', 'f1e2d3c4b5a6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
