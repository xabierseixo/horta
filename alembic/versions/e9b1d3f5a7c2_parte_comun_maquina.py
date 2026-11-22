"""parte común: máquina nos traballos onde pode haber unha

Revision ID: e9b1d3f5a7c2
Revises: d7f9b1c3e5a8
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9b1d3f5a7c2'
down_revision: Union[str, Sequence[str], None] = 'd7f9b1c3e5a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Traballos onde pode haber unha máquina e aínda non se podía indicar
_SEN_MAQUINA = ("rega", "tratamento_instalacion", "movemento_animal", "producion_animal")


def upgrade() -> None:
    """Upgrade schema."""
    for taboa in _SEN_MAQUINA:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("maquina_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_maquina_id", "maquina", ["maquina_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _SEN_MAQUINA:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_maquina_id", type_="foreignkey")
            batch.drop_column("maquina_id")
