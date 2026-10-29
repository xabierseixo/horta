"""o tempo: estacións de MeteoGalicia, o tempo de cada día e tempo_id na parte común

Revision ID: d7b9f1a3c5e8
Revises: c6a8e0b2d4f7
Create Date: 2026-10-29 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7b9f1a3c5e8'
down_revision: Union[str, Sequence[str], None] = 'c6a8e0b2d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Os traballos coa parte común (horta.models.traballo.ParteComun)
_TRABALLOS = ("abonado", "analise", "coidado_animal", "colleita", "entrada_produto", "labor",
              "lote_saida", "movemento_animal", "outro_traballo", "pastoreo",
              "producion_animal", "rega", "tratamento_fito", "tratamento_instalacion")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "estacion_meteo",
        sa.Column("id", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("nome", sa.String(length=120), nullable=False),
        sa.Column("concello", sa.String(length=120), nullable=True),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lon", sa.Float(), nullable=False),
        sa.Column("altitude", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "tempo_dia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("estacion_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("t_min", sa.Float(), nullable=True),
        sa.Column("t_max", sa.Float(), nullable=True),
        sa.Column("t_media", sa.Float(), nullable=True),
        sa.Column("choiva", sa.Float(), nullable=True),
        sa.Column("vento_medio", sa.Float(), nullable=True),
        sa.Column("refacho", sa.Float(), nullable=True),
        sa.Column("humidade", sa.Float(), nullable=True),
        sa.Column("et0", sa.Float(), nullable=True),
        sa.Column("fonte", sa.String(length=50), nullable=False),
        sa.Column("consultado", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["estacion_id"], ["estacion_meteo.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("estacion_id", "data"),
    )
    op.create_index(op.f("ix_tempo_dia_estacion_id"), "tempo_dia", ["estacion_id"],
                    unique=False)
    for taboa in ("horta", "parcela"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("concello_ine", sa.String(length=5), nullable=True))
            batch.add_column(sa.Column("estacion_meteo_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_estacion_meteo_id", "estacion_meteo",
                                     ["estacion_meteo_id"], ["id"])
    for taboa in _TRABALLOS:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("tempo_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_tempo_id", "tempo_dia", ["tempo_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _TRABALLOS:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_tempo_id", type_="foreignkey")
            batch.drop_column("tempo_id")
    for taboa in ("horta", "parcela"):
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_estacion_meteo_id", type_="foreignkey")
            batch.drop_column("estacion_meteo_id")
            batch.drop_column("concello_ine")
    op.drop_index(op.f("ix_tempo_dia_estacion_id"), table_name="tempo_dia")
    op.drop_table("tempo_dia")
    op.drop_table("estacion_meteo")
