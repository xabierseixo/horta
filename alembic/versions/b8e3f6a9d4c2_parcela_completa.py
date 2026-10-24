"""parcela completa (REA bloque 12, DGC)

Revision ID: b8e3f6a9d4c2
Revises: a7d2e5f8c3b1
Create Date: 2026-10-23 14:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8e3f6a9d4c2"
down_revision: Union[str, Sequence[str], None] = "a7d2e5f8c3b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("sigpac_agregado", sa.String(10), nullable=True))
        batch.add_column(sa.Column("sigpac_zona", sa.String(10), nullable=True))
        batch.add_column(sa.Column("referencia_catastral", sa.String(20), nullable=True))
        batch.add_column(sa.Column("rexime_tenencia", sa.String(20), nullable=True))
        batch.add_column(sa.Column("nif_arrendador", sa.String(9), nullable=True))
        batch.add_column(
            sa.Column("pequena_superficie", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("data_alta", sa.Date(), nullable=True))
        batch.add_column(sa.Column("data_baixa", sa.Date(), nullable=True))
        batch.add_column(sa.Column("causa_baixa", sa.String(20), nullable=True))
        batch.add_column(sa.Column("orixe_auga", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("parcela") as batch:
        batch.drop_column("orixe_auga")
        batch.drop_column("causa_baixa")
        batch.drop_column("data_baixa")
        batch.drop_column("data_alta")
        batch.drop_column("pequena_superficie")
        batch.drop_column("nif_arrendador")
        batch.drop_column("rexime_tenencia")
        batch.drop_column("referencia_catastral")
        batch.drop_column("sigpac_zona")
        batch.drop_column("sigpac_agregado")
