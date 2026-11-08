"""seguimento de pragas: observacions e limiares

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-11-08 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "observacion_praga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("problema_tipo", sa.String(length=20), nullable=False),
        sa.Column("problema_codigo", sa.String(length=20), nullable=False),
        sa.Column("metodo", sa.String(length=20), nullable=False),
        sa.Column("conto", sa.Float(), nullable=True),
        sa.Column("unidade_conto", sa.String(length=30), nullable=True),
        sa.Column("nivel", sa.String(length=10), nullable=True),
        sa.Column("estado_fenoloxico", sa.String(length=20), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("tempo_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["tempo_id"], ["tempo_dia.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(
        op.f("ix_observacion_praga_cultivo_id"), "observacion_praga", ["cultivo_id"], unique=False
    )
    op.create_index(
        op.f("ix_observacion_praga_horta_id"), "observacion_praga", ["horta_id"], unique=False
    )

    op.create_table(
        "limiar_praga",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("cultivo_siex_codigo", sa.Integer(), nullable=True),
        sa.Column("problema_tipo", sa.String(length=20), nullable=False),
        sa.Column("problema_codigo", sa.String(length=20), nullable=False),
        sa.Column("metodo", sa.String(length=20), nullable=False),
        sa.Column("unidade_conto", sa.String(length=30), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("fonte", sa.String(length=300), nullable=False),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_limiar_praga_horta_id"), "limiar_praga", ["horta_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_limiar_praga_horta_id"), table_name="limiar_praga")
    op.drop_table("limiar_praga")
    op.drop_index(op.f("ix_observacion_praga_horta_id"), table_name="observacion_praga")
    op.drop_index(op.f("ix_observacion_praga_cultivo_id"), table_name="observacion_praga")
    op.drop_table("observacion_praga")
