"""add playground detail fields, mood tags, and save feature

Revision ID: 2ab97c2eacc9
Revises: 3948b7674b46
Create Date: 2026-07-29 15:13:26.831299

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2ab97c2eacc9'
down_revision: Union[str, None] = '3948b7674b46'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    condition_status = sa.Enum('VERY_CLEAN', 'AVERAGE', 'NEEDS_CARE', name='condition_status')
    playground_size = sa.Enum('SMALL', 'MEDIUM', 'LARGE', name='playground_size')
    play_duration = sa.Enum('MIN_30', 'HOUR_1', 'HOUR_2_PLUS', name='play_duration')
    nature_feature = sa.Enum('MANY_TREES', 'SHADY', 'IN_FOREST', 'IN_PARK', name='nature_feature')
    pet_policy = sa.Enum('ALLOWED', 'NOT_ALLOWED', name='pet_policy')
    nearby_facility = sa.Enum(
        'CONVENIENCE_STORE', 'CAFE', 'RESTROOM', 'PHARMACY', 'HOSPITAL', 'PARKING',
        name='nearby_facility',
    )
    smoking_status = sa.Enum('MANY_SMOKERS', 'NO_SMOKING_ZONE', name='smoking_status')
    wheeled_access_type = sa.Enum('KICKBOARD', 'BICYCLE', name='wheeled_access_type')
    access_level = sa.Enum('EASY', 'MODERATE', 'DIFFICULT', name='access_level')
    road_safety_level = sa.Enum('VERY_SAFE', 'MODERATE', 'DANGEROUS', name='road_safety_level')
    mood_tag = sa.Enum(
        'QUIET', 'ACTIVE', 'PHOTOGENIC', 'SPACIOUS', 'NEWLY_BUILT', 'WELL_MAINTAINED',
        'HIDDEN_GEM', 'RAINY_DAY_OK', 'SUMMER_PICK', 'WINTER_PICK', 'STROLLER_FRIENDLY',
        'FIRST_PLAYGROUND', 'DATE_SPOT', 'FOREST_VIBE', 'LOTS_TO_DO',
        name='mood_tag',
    )

    # ARRAY(Enum(...))는 autogenerate가 enum 타입 생성을 빠뜨리므로 먼저 명시적으로 생성한다.
    for enum_type in (
        condition_status, playground_size, play_duration, nature_feature, pet_policy,
        nearby_facility, smoking_status, wheeled_access_type, access_level, road_safety_level,
        mood_tag,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table('playground_saves',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('playground_id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['playground_id'], ['playgrounds.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('playground_id', 'user_id', name='uq_playground_save')
    )
    op.add_column('playgrounds', sa.Column('condition_status', condition_status, nullable=True))
    op.add_column('playgrounds', sa.Column('size', playground_size, nullable=True))
    op.add_column('playgrounds', sa.Column('play_duration', play_duration, nullable=True))
    op.add_column('playgrounds', sa.Column('recommended_age', sa.SmallInteger(), nullable=True))
    op.add_column('playgrounds', sa.Column('recommend_rating', sa.SmallInteger(), nullable=True))
    op.add_column('playgrounds', sa.Column('nature_features', postgresql.ARRAY(nature_feature), nullable=True))
    op.add_column('playgrounds', sa.Column('operating_season', sa.String(length=100), nullable=True))
    op.add_column('playgrounds', sa.Column('pet_policy', pet_policy, nullable=True))
    op.add_column('playgrounds', sa.Column('nearby_facilities', postgresql.ARRAY(nearby_facility), nullable=True))
    op.add_column('playgrounds', sa.Column('smoking_status', smoking_status, nullable=True))
    op.add_column('playgrounds', sa.Column('wheeled_access', postgresql.ARRAY(wheeled_access_type), nullable=True))
    op.add_column('playgrounds', sa.Column('stroller_access_level', access_level, nullable=True))
    op.add_column('playgrounds', sa.Column('road_safety', road_safety_level, nullable=True))
    op.add_column('playgrounds', sa.Column('mood_tags', postgresql.ARRAY(mood_tag), nullable=True))
    op.add_column('playgrounds', sa.Column('view_count', sa.Integer(), server_default='0', nullable=False))

    op.create_check_constraint(
        'ck_playground_recommended_age',
        'playgrounds',
        'recommended_age IS NULL OR (recommended_age BETWEEN 0 AND 15)',
    )
    op.create_check_constraint(
        'ck_playground_recommend_rating',
        'playgrounds',
        'recommend_rating IS NULL OR (recommend_rating BETWEEN 1 AND 5)',
    )


def downgrade() -> None:
    op.drop_constraint('ck_playground_recommend_rating', 'playgrounds', type_='check')
    op.drop_constraint('ck_playground_recommended_age', 'playgrounds', type_='check')

    op.drop_column('playgrounds', 'view_count')
    op.drop_column('playgrounds', 'mood_tags')
    op.drop_column('playgrounds', 'road_safety')
    op.drop_column('playgrounds', 'stroller_access_level')
    op.drop_column('playgrounds', 'wheeled_access')
    op.drop_column('playgrounds', 'smoking_status')
    op.drop_column('playgrounds', 'nearby_facilities')
    op.drop_column('playgrounds', 'pet_policy')
    op.drop_column('playgrounds', 'operating_season')
    op.drop_column('playgrounds', 'nature_features')
    op.drop_column('playgrounds', 'recommend_rating')
    op.drop_column('playgrounds', 'recommended_age')
    op.drop_column('playgrounds', 'play_duration')
    op.drop_column('playgrounds', 'size')
    op.drop_column('playgrounds', 'condition_status')
    op.drop_table('playground_saves')

    bind = op.get_bind()
    for type_name in (
        'mood_tag', 'road_safety_level', 'access_level', 'wheeled_access_type', 'smoking_status',
        'nearby_facility', 'pet_policy', 'nature_feature', 'play_duration', 'playground_size',
        'condition_status',
    ):
        sa.Enum(name=type_name).drop(bind, checkfirst=True)
