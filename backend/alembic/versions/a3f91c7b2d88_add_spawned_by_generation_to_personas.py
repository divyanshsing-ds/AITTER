"""add_spawned_by_generation_to_personas

Revision ID: a3f91c7b2d88
Revises: 371048119e7a
Create Date: 2026-03-18 16:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a3f91c7b2d88'
down_revision: Union[str, Sequence[str], None] = '371048119e7a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('ai_personas', sa.Column('spawned_by', sa.String(length=100), nullable=True))
    op.add_column('ai_personas', sa.Column('generation', sa.Integer(), nullable=True, server_default='0'))


def downgrade() -> None:
    op.drop_column('ai_personas', 'generation')
    op.drop_column('ai_personas', 'spawned_by')
