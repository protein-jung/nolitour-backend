"""add rating and review tags to comments

Revision ID: b9a912bb8f9f
Revises: c81f68eb6a51
Create Date: 2026-07-22 14:55:39.474221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b9a912bb8f9f'
down_revision: Union[str, None] = 'c81f68eb6a51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # age_group 타입은 이미 존재하므로 재생성하지 않는다. risk_tag는 새 타입이라 먼저 생성해야
    # ARRAY(Enum(...)) 컬럼 추가 시 "type does not exist" 오류가 나지 않는다.
    risk_tag = sa.Enum('NEAR_ROAD', 'MANY_BUGS', 'POORLY_MAINTAINED', name='risk_tag')
    risk_tag.create(bind, checkfirst=True)

    age_group = postgresql.ENUM(name='age_group', create_type=False)

    op.add_column('playground_comments', sa.Column('rating', sa.SmallInteger(), nullable=True))
    op.add_column('playground_comments', sa.Column('recommended_ages', postgresql.ARRAY(age_group), nullable=True))
    op.add_column('playground_comments', sa.Column('risk_tags', postgresql.ARRAY(risk_tag), nullable=True))
    op.create_check_constraint(
        'ck_comment_rating_range', 'playground_comments', 'rating IS NULL OR (rating BETWEEN 1 AND 5)'
    )


def downgrade() -> None:
    op.drop_constraint('ck_comment_rating_range', 'playground_comments', type_='check')
    op.drop_column('playground_comments', 'risk_tags')
    op.drop_column('playground_comments', 'recommended_ages')
    op.drop_column('playground_comments', 'rating')
    sa.Enum(name='risk_tag').drop(op.get_bind(), checkfirst=True)
