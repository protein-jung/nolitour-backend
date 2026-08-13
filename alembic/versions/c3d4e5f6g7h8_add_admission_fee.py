"""add admission fee fields

Revision ID: c3d4e5f6g7h8
Revises: b2d3e4f5g6h7
Create Date: 2026-08-13 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = 'b2d3e4f5g6h7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    admission_fee_type = sa.Enum('FREE', 'PAID', name='admission_fee_type')
    admission_fee_type.create(bind, checkfirst=True)

    op.add_column('playgrounds', sa.Column('admission_fee_type', admission_fee_type, nullable=True))
    op.add_column('playgrounds', sa.Column('admission_fee', sa.Integer(), nullable=True))

    op.create_check_constraint(
        'ck_playground_admission_fee',
        'playgrounds',
        'admission_fee IS NULL OR admission_fee >= 0',
    )


def downgrade() -> None:
    op.drop_constraint('ck_playground_admission_fee', 'playgrounds', type_='check')
    op.drop_column('playgrounds', 'admission_fee')
    op.drop_column('playgrounds', 'admission_fee_type')

    sa.Enum(name='admission_fee_type').drop(op.get_bind(), checkfirst=True)
