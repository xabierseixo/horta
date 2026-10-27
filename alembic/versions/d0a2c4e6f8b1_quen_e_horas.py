"""quen fixo cada traballo e cantas horas

Revision ID: d0a2c4e6f8b1
Revises: c9e1a3b5d7f0
Create Date: 2026-10-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0a2c4e6f8b1'
down_revision: Union[str, Sequence[str], None] = 'c9e1a3b5d7f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Táboa -> (columna da persoa ou None se xa a ten, columna das horas)
_COLUMNAS = {
    "rega": ("persoa_id", "horas"),
    "colleita": ("persoa_id", "horas"),
    "analise": ("persoa_id", "horas"),
    "tratamento_instalacion": ("persoa_id", "horas"),
    "labor": (None, "horas"),
    "abonado": (None, "horas"),
    "cultivo": ("sementeira_persoa_id", "sementeira_horas"),
}


def upgrade() -> None:
    """Upgrade schema."""
    for taboa, (persoa, horas) in _COLUMNAS.items():
        with op.batch_alter_table(taboa) as batch:
            if persoa:
                batch.add_column(sa.Column(persoa, sa.Integer(), nullable=True))
                batch.create_foreign_key(f"fk_{taboa}_{persoa}", "persoa", [persoa], ["id"])
            batch.add_column(sa.Column(horas, sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    for taboa, (persoa, horas) in _COLUMNAS.items():
        with op.batch_alter_table(taboa) as batch:
            batch.drop_column(horas)
            if persoa:
                batch.drop_constraint(f"fk_{taboa}_{persoa}", type_="foreignkey")
                batch.drop_column(persoa)
