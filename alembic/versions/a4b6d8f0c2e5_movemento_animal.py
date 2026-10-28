"""entradas e saídas de animais; especie do catálogo oficial

Revision ID: a4b6d8f0c2e5
Revises: f3a5c7e9b1d4
Create Date: 2026-10-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b6d8f0c2e5'
down_revision: Union[str, Sequence[str], None] = 'f3a5c7e9b1d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "movemento_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Integer(), nullable=False),
        sa.Column("identificacion", sa.String(length=500), nullable=True),
        sa.Column("titular", sa.String(length=300), nullable=True),
        sa.Column("rega", sa.String(length=20), nullable=True),
        sa.Column("codigo_movemento", sa.String(length=50), nullable=True),
        sa.Column("causa", sa.String(length=300), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movemento_animal_horta_id", "movemento_animal", ["horta_id"])
    op.create_index("ix_movemento_animal_animal_id", "movemento_animal", ["animal_id"])
    with op.batch_alter_table("animal") as batch:
        batch.add_column(sa.Column("especie_codigo", sa.String(length=20), nullable=True))
    # Os grupos que xa existen: os seus animais entran como movemento inicial na data de alta
    op.execute(
        "INSERT INTO movemento_animal (horta_id, animal_id, data, tipo, cantidade, baixa, "
        "created_at) SELECT horta_id, id, data_alta, 'inicial', cantidade, 0, CURRENT_TIMESTAMP "
        "FROM animal WHERE cantidade > 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("animal") as batch:
        batch.drop_column("especie_codigo")
    op.drop_index("ix_movemento_animal_animal_id", table_name="movemento_animal")
    op.drop_index("ix_movemento_animal_horta_id", table_name="movemento_animal")
    op.drop_table("movemento_animal")
