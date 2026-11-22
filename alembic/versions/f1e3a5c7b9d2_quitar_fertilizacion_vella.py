"""quitar a fertilización vella (substituída por abonado)

Revision ID: f1e3a5c7b9d2
Revises: 230c962c9af9
Create Date: 2026-10-25 02:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1e3a5c7b9d2"
down_revision: Union[str, Sequence[str], None] = "230c962c9af9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("fertilizacion")


def downgrade() -> None:
    op.create_table(
        "fertilizacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("superficie", sa.Float(), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("produto", sa.String(length=200), nullable=False),
        sa.Column("dose", sa.String(length=100), nullable=True),
        sa.Column("n", sa.Float(), nullable=True),
        sa.Column("p", sa.Float(), nullable=True),
        sa.Column("k", sa.Float(), nullable=True),
        sa.Column("carbono_organico", sa.Float(), nullable=True),
        sa.Column("micronutrientes", sa.String(length=300), nullable=True),
        sa.Column("asesoramento_recibido", sa.String(length=300), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
