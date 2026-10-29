"""o tempo: temperatura do chan, horas de frío e de sol e balance hídrico

Revision ID: a0e2c4f6b8d3
Revises: f9d1b3c5e7a2
Create Date: 2026-10-29 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0e2c4f6b8d3'
down_revision: Union[str, Sequence[str], None] = 'f9d1b3c5e7a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CAMPOS = ("t_chan", "horas_frio", "horas_sol", "balance_hidrico")


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tempo_dia") as batch:
        for campo in _CAMPOS:
            batch.add_column(sa.Column(campo, sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tempo_dia") as batch:
        for campo in _CAMPOS:
            batch.drop_column(campo)
