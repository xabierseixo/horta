"""campos do CUE opcionais ao apuntar (o caderno avisa do que falta)

Revision ID: c9e1a3b5d7f0
Revises: b8d0f2a4c6e9
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e1a3b5d7f0'
down_revision: Union[str, Sequence[str], None] = 'b8d0f2a4c6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OPCIONAIS = {
    "rega": (("superficie_ha", sa.Float()), ("sistema_rega", sa.String(length=20)),
             ("cantidade", sa.Float())),
    "labor": (("superficie_ha", sa.Float()),),
    "abonado": (("superficie_ha", sa.Float()), ("tipo_fertilizacion", sa.String(length=20)),
                ("metodo", sa.String(length=20))),
}


def upgrade() -> None:
    """Upgrade schema."""
    for taboa, columnas in _OPCIONAIS.items():
        with op.batch_alter_table(taboa) as batch:
            for nome, tipo in columnas:
                batch.alter_column(nome, existing_type=tipo, nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    for taboa, columnas in _OPCIONAIS.items():
        with op.batch_alter_table(taboa) as batch:
            for nome, tipo in columnas:
                batch.alter_column(nome, existing_type=tipo, nullable=False)
