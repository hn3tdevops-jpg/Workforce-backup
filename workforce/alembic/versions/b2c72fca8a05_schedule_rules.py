"""schedule_rules

Revision ID: b2c72fca8a05
Revises: b7c2e4f1a9d3
Create Date: 2026-02-22 11:04:07.245571

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c72fca8a05'
down_revision: Union[str, None] = 'b7c2e4f1a9d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('schedule_rules',
    sa.Column('business_id', sa.String(length=36), nullable=False),
    sa.Column('raw_text', sa.Text(), nullable=False),
    sa.Column('rule_type', sa.Enum('coverage', 'availability', 'fairness', 'constraint', name='schedule_rule_type'), nullable=False),
    sa.Column('parsed_json', sa.Text(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_by_user_id', sa.String(length=36), nullable=True),
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('schedule_rules', schema=None) as batch_op:
        batch_op.create_index('ix_schedule_rules_biz_active', ['business_id', 'is_active'], unique=False)
        batch_op.create_index(batch_op.f('ix_schedule_rules_business_id'), ['business_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('schedule_rules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_schedule_rules_business_id'))
        batch_op.drop_index('ix_schedule_rules_biz_active')

    op.drop_table('schedule_rules')
