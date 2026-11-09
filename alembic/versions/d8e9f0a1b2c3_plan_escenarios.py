"""plan de empresa: escenarios e orientacion recan

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
Create Date: 2026-11-09 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd8e9f0a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('plan_empresa') as batch:
        batch.add_column(sa.Column('escenario_pct', sa.Float(), nullable=False,
                                   server_default='20'))
        batch.add_column(sa.Column('ote_recan', sa.String(length=10), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('plan_empresa') as batch:
        batch.drop_column('ote_recan')
        batch.drop_column('escenario_pct')
