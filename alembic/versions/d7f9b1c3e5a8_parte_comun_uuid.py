"""parte común: identificador do móbil en todos os traballos

Revision ID: d7f9b1c3e5a8
Revises: c6e8a0b2d4f7
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f9b1c3e5a8'
down_revision: Union[str, Sequence[str], None] = 'c6e8a0b2d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Táboas que aínda non tiñan o identificador do móbil
_SEN_UUID = ("labor", "tratamento_fito", "tratamento_instalacion", "abonado", "rega",
             "analise", "coidado_animal", "movemento_animal", "tarefa", "cultivo")


def upgrade() -> None:
    """Upgrade schema."""
    for taboa in _SEN_UUID:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("uuid", sa.String(length=36), nullable=True))
            batch.create_unique_constraint(f"uq_{taboa}_uuid", ["uuid"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _SEN_UUID:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"uq_{taboa}_uuid", type_="unique")
            batch.drop_column("uuid")
