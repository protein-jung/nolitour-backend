"""add viewer_key to playground views

Revision ID: a1c2d3e4f5g6
Revises: c45c090031b5
Create Date: 2026-08-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c2d3e4f5g6'
down_revision: Union[str, None] = 'c45c090031b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('playground_views', sa.Column('viewer_key', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('playground_views', 'viewer_key')
