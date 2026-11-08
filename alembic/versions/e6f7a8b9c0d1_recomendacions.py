"""recomendacións do asesor fitosanitario

Revision ID: e6f7a8b9c0d1
Revises: d4e5f6a1b2c3
Create Date: 2026-11-08 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a1b2c3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "recomendacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("asesor_persoa_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("valida_ata", sa.Date(), nullable=True),
        sa.Column("cultivos", sa.JSON(), nullable=False),
        sa.Column("problemas", sa.JSON(), nullable=False),
        sa.Column("xustificacions", sa.JSON(), nullable=False),
        sa.Column("produtos", sa.JSON(), nullable=False),
        sa.Column("medidas", sa.JSON(), nullable=False),
        sa.Column("observacions", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(length=12), nullable=False),
        sa.Column("motivo_descarte", sa.String(length=300), nullable=True),
        sa.Column("tratamento_id", sa.Integer(), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["asesor_persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["tratamento_id"], ["tratamento_fito.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recomendacion_horta_id"), "recomendacion", ["horta_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_recomendacion_horta_id"), table_name="recomendacion")
    op.drop_table("recomendacion")
