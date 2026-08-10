"""add sports facilities field

Revision ID: b2d3e4f5g6h7
Revises: a1c2d3e4f5g6
Create Date: 2026-08-10 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b2d3e4f5g6h7'
down_revision: Union[str, None] = 'a1c2d3e4f5g6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    sports_facility = sa.Enum(
        'SOCCER_FIELD', 'BASKETBALL_COURT', 'BADMINTON_COURT', 'VOLLEYBALL_COURT',
        'GRASS_FIELD', 'OUTDOOR_GYM', 'GATEBALL_COURT',
        name='sports_facility',
    )
    # ARRAY(Enum(...))는 autogenerate가 enum 타입 생성을 빠뜨리므로 먼저 명시적으로 생성한다.
    sports_facility.create(bind, checkfirst=True)

    op.add_column('playgrounds', sa.Column('sports_facilities', postgresql.ARRAY(sports_facility), nullable=True))


def downgrade() -> None:
    op.drop_column('playgrounds', 'sports_facilities')
    sa.Enum(name='sports_facility').drop(op.get_bind(), checkfirst=True)
