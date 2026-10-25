"""quitar os campos vellos do cultivo (substituídos por data_inicio/data_fin e colleitas)

Revision ID: b1d3f5a7c9e2
Revises: d6f8b0c2e4a7
Create Date: 2026-10-25 04:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1d3f5a7c9e2"
down_revision: Union[str, Sequence[str], None] = "d6f8b0c2e4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Non perder datas: pásanse aos campos novos se estes están baleiros
    op.execute(
        "UPDATE cultivo SET "
        "tipo_inicio = COALESCE(tipo_inicio, CASE WHEN data_sementeira IS NOT NULL "
        "THEN 'sementeira' WHEN data_plantacion IS NOT NULL THEN 'plantacion' END), "
        "data_inicio = COALESCE(data_inicio, data_sementeira, data_plantacion), "
        "data_fin = COALESCE(data_fin, data_colleita_real)"
    )
    with op.batch_alter_table("cultivo") as taboa:
        for columna in ("data_sementeira", "data_plantacion", "data_colleita_real",
                        "cantidade", "unidade"):
            taboa.drop_column(columna)


def downgrade() -> None:
    with op.batch_alter_table("cultivo") as taboa:
        taboa.add_column(sa.Column("data_sementeira", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("data_plantacion", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("data_colleita_real", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("cantidade", sa.Float(), nullable=True))
        taboa.add_column(sa.Column("unidade", sa.String(length=30), nullable=True))
