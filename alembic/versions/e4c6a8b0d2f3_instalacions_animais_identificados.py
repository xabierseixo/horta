"""instalacións e animais identificados

Revision ID: e4c6a8b0d2f3
Revises: d3b5f7a9c1e2
Create Date: 2026-10-29 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4c6a8b0d2f3'
down_revision: Union[str, Sequence[str], None] = 'd3b5f7a9c1e2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "instalacion",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("horta_id", sa.Integer(), sa.ForeignKey("horta.id"), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("enderezo", sa.String(length=200), nullable=True),
        sa.Column("referencia_catastral", sa.String(length=30), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False),
    )
    op.create_index(op.f("ix_instalacion_horta_id"), "instalacion", ["horta_id"])
    op.create_table(
        "animal_identificado",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("animal_id", sa.Integer(), sa.ForeignKey("animal.id"), nullable=False),
        sa.Column("identificador", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=80), nullable=True),
        sa.Column("sexo", sa.String(length=10), nullable=True),
        sa.Column("data_nacemento", sa.Date(), nullable=True),
        sa.Column("data_alta", sa.Date(), nullable=False),
        sa.Column("data_baixa", sa.Date(), nullable=True),
        sa.Column("notas", sa.String(length=500), nullable=True),
    )
    op.create_index(op.f("ix_animal_identificado_animal_id"), "animal_identificado",
                    ["animal_id"])
    for taboa in ("animal", "outro_traballo"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("instalacion_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_instalacion", "instalacion",
                                     ["instalacion_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in ("animal", "outro_traballo"):
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_instalacion", type_="foreignkey")
            batch.drop_column("instalacion_id")
    op.drop_index(op.f("ix_animal_identificado_animal_id"), table_name="animal_identificado")
    op.drop_table("animal_identificado")
    op.drop_index(op.f("ix_instalacion_horta_id"), table_name="instalacion")
    op.drop_table("instalacion")
