"""visitas de campo: táboa e claves en observacións e recomendacións

Revision ID: a7b8c9d0e1f2
Revises: f8a4c2e0b1d3
Create Date: 2026-11-08 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, Sequence[str], None] = 'f8a4c2e0b1d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "visita_campo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("asesor_persoa_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("hora_inicio", sa.Time(), nullable=True),
        sa.Column("cultivos", sa.JSON(), nullable=False),
        sa.Column("estado_xeral", sa.Text(), nullable=True),
        sa.Column("conclusions", sa.Text(), nullable=True),
        sa.Column("proxima_visita", sa.Date(), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["asesor_persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_visita_campo_horta_id"),
        "visita_campo",
        ["horta_id"],
        unique=False,
    )

    with op.batch_alter_table("observacion_praga") as batch:
        batch.add_column(sa.Column("visita_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_observacion_praga_visita_id", "visita_campo", ["visita_id"], ["id"]
        )

    with op.batch_alter_table("recomendacion") as batch:
        batch.add_column(sa.Column("visita_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_recomendacion_visita_id", "visita_campo", ["visita_id"], ["id"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("recomendacion") as batch:
        batch.drop_column("visita_id")
    with op.batch_alter_table("observacion_praga") as batch:
        batch.drop_column("visita_id")
    op.drop_index(
        op.f("ix_visita_campo_horta_id"),
        table_name="visita_campo",
    )
    op.drop_table("visita_campo")
