"""
Add primary_location_id and updated_at to memberships

Revision ID: 20260425_add_membership_fields
Revises: 20260425_add_user_profile_fields
Create Date: 2026-04-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260425_add_membership_fields'
down_revision = ('20260425_add_user_profile_fields',)
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        batch_op.add_column(sa.Column('primary_location_id', sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))


def downgrade():
    with op.batch_alter_table('memberships', schema=None) as batch_op:
        try:
            batch_op.drop_column('updated_at')
        except Exception:
            pass
        batch_op.drop_column('primary_location_id')
