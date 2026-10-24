"""quitar o tratamento vello (os datos están en tratamento_fito)

Revision ID: c7f2a9d1e4b6
Revises: b8e3f6a9d4c2
Create Date: 2026-10-24 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7f2a9d1e4b6"
down_revision: Union[str, Sequence[str], None] = "b8e3f6a9d4c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("tratamento")


def downgrade() -> None:
    op.create_table(
        "tratamento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("praga", sa.String(length=200), nullable=False),
        sa.Column("superficie_tratada", sa.Float(), nullable=True),
        sa.Column("produto", sa.String(length=200), nullable=False),
        sa.Column("numero_rexistro_produto", sa.String(length=50), nullable=True),
        sa.Column("dose", sa.String(length=100), nullable=True),
        sa.Column("eficacia", sa.String(length=200), nullable=True),
        sa.Column("aplicador", sa.String(length=200), nullable=False),
        sa.Column("equipo_aplicador", sa.String(length=200), nullable=True),
        sa.Column("persoas_asesoramento", sa.String(length=200), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
