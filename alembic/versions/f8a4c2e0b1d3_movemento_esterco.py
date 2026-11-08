"""movemento de esterco: cesións e recepcións

Revision ID: f8a4c2e0b1d3
Revises: c2784bdf2b44
Create Date: 2026-11-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8a4c2e0b1d3'
down_revision: Union[str, Sequence[str], None] = 'f7a8b9c0d1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "movemento_esterco",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("outra_parte_id", sa.Integer(), nullable=False),
        sa.Column("outra_parte_rega", sa.String(length=20), nullable=True),
        sa.Column("tipo_explotacion", sa.String(length=100), nullable=False),
        sa.Column("tipo_animais", sa.String(length=30), nullable=False),
        sa.Column("material", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(length=10), nullable=False),
        sa.Column("n_total", sa.Float(), nullable=True),
        sa.Column("p2o5", sa.Float(), nullable=True),
        sa.Column("k2o", sa.Float(), nullable=True),
        sa.Column("materia_organica", sa.Float(), nullable=True),
        sa.Column("orixe_composicion", sa.String(length=20), nullable=True),
        sa.Column("parcelas_destino", sa.String(length=300), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("tempo_id", sa.Integer(), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["outra_parte_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["tempo_id"], ["tempo_dia.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index(
        op.f("ix_movemento_esterco_horta_id"),
        "movemento_esterco",
        ["horta_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_movemento_esterco_outra_parte_id"),
        "movemento_esterco",
        ["outra_parte_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_movemento_esterco_outra_parte_id"),
        table_name="movemento_esterco",
    )
    op.drop_index(
        op.f("ix_movemento_esterco_horta_id"),
        table_name="movemento_esterco",
    )
    op.drop_table("movemento_esterco")
