"""catálogo oficial de produtos fertilizantes (DETALLE_MATERIAL_FERT)

Revision ID: d8a1f3c5e7b9
Revises: c7f2a9d1e4b6
Create Date: 2026-10-25 10:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8a1f3c5e7b9"
down_revision: Union[str, Sequence[str], None] = "c7f2a9d1e4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fertilizante_siex",
        sa.Column("codigo", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("material", sa.String(length=20), nullable=False),
        sa.Column("clase", sa.String(length=60), nullable=True),
        sa.Column("subclase", sa.String(length=60), nullable=True),
        sa.Column("nome", sa.String(length=300), nullable=False),
        sa.Column("fabricante", sa.String(length=200), nullable=True),
        sa.Column("n_pct", sa.Float(), nullable=False),
        sa.Column("p2o5_pct", sa.Float(), nullable=False),
        sa.Column("k2o_pct", sa.Float(), nullable=False),
        sa.Column("liquido", sa.Boolean(), nullable=False),
        sa.Column("densidade", sa.Float(), nullable=True),
        sa.Column("inhibidor_nitrificacion", sa.Boolean(), nullable=False),
        sa.Column("inhibidor_ureasa", sa.Boolean(), nullable=False),
        sa.Column("data_baixa", sa.Date(), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["catalogo_version.id"]),
        sa.PrimaryKeyConstraint("codigo"),
    )
    op.create_index("ix_fertilizante_siex_material", "fertilizante_siex", ["material"])


def downgrade() -> None:
    op.drop_index("ix_fertilizante_siex_material", table_name="fertilizante_siex")
    op.drop_table("fertilizante_siex")
