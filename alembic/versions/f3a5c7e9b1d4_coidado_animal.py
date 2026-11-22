"""coidado e saúde dos animais; a tarefa pode referirse a un grupo de animais

Revision ID: f3a5c7e9b1d4
Revises: e1b3d5f7a9c2
Create Date: 2026-10-28 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a5c7e9b1d4'
down_revision: Union[str, Sequence[str], None] = 'e1b3d5f7a9c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "coidado_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("descricion", sa.String(length=500), nullable=True),
        sa.Column("num_animais", sa.Integer(), nullable=True),
        sa.Column("identificacion", sa.String(length=500), nullable=True),
        sa.Column("medicamento", sa.String(length=250), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=True),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("provedor", sa.String(length=300), nullable=True),
        sa.Column("proba_compra", sa.String(length=100), nullable=True),
        sa.Column("veterinario", sa.String(length=200), nullable=True),
        sa.Column("receita", sa.String(length=50), nullable=True),
        sa.Column("tempo_espera_dias", sa.Integer(), nullable=True),
        sa.Column("duracion_dias", sa.Integer(), nullable=True),
        sa.Column("visitante", sa.String(length=200), nullable=True),
        sa.Column("matricula", sa.String(length=20), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("maquina_id", sa.Integer(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["maquina_id"], ["maquina.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coidado_animal_horta_id", "coidado_animal", ["horta_id"])
    op.create_index("ix_coidado_animal_animal_id", "coidado_animal", ["animal_id"])
    with op.batch_alter_table("tarefa") as batch:
        batch.add_column(sa.Column("animal_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tarefa_animal_id", "animal", ["animal_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.drop_constraint("fk_tarefa_animal_id", type_="foreignkey")
        batch.drop_column("animal_id")
    op.drop_index("ix_coidado_animal_animal_id", table_name="coidado_animal")
    op.drop_index("ix_coidado_animal_horta_id", table_name="coidado_animal")
    op.drop_table("coidado_animal")
