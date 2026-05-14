"""merge heads for RBAC and hkops

Revision ID: 8b9724120087
Revises: 432688e91336, zz_add_rbac_tables
Create Date: 2026-03-04 01:32:49.733055

"""
from typing import Sequence, Union



# revision identifiers, used by Alembic.
revision: str = '8b9724120087'
down_revision: Union[str, None] = ('432688e91336', 'zz_add_rbac_tables')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
