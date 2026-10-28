"""persoas e entidades: papeis (persoa_papel) e rexistros de cada persoa

Revision ID: c3f5a7b9d1e6
Revises: b2e4a6c8d0f5
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3f5a7b9d1e6'
down_revision: Union[str, Sequence[str], None] = 'b2e4a6c8d0f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_BOOLEANOS = {"e_titular": "titular", "e_traballador": "traballador",
              "e_aplicador": "aplicador", "e_asesor": "asesor"}
_NOVOS = (("tipo", sa.String(10)), ("concello_codigo", sa.String(5)), ("pais", sa.String(50)),
          ("rega", sa.String(14)), ("reaga", sa.String(14)), ("nima", sa.String(50)),
          ("ropveg", sa.String(50)), ("rexistro_dixital", sa.String(50)),
          ("num_asesoramento", sa.String(50)))


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "persoa_papel",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=False),
        sa.Column("papel", sa.String(length=20), nullable=False),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("persoa_id", "papel"),
    )
    op.create_index(op.f("ix_persoa_papel_persoa_id"), "persoa_papel", ["persoa_id"])
    with op.batch_alter_table("persoa") as batch:
        for nome, tipo in _NOVOS:
            batch.add_column(sa.Column(nome, tipo, nullable=True))
        batch.alter_column("nome", type_=sa.String(200))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE persoa SET tipo = 'persoa'"))
    for columna, papel in _BOOLEANOS.items():
        conn.execute(sa.text(
            f"INSERT INTO persoa_papel (persoa_id, papel) SELECT id, '{papel}' FROM persoa "
            f"WHERE {columna}"))
    # Ata agora todas as persoas eran do equipo: as que non tiñan función traballan nela
    conn.execute(sa.text(
        "INSERT INTO persoa_papel (persoa_id, papel) SELECT id, 'traballador' FROM persoa "
        "WHERE id NOT IN (SELECT persoa_id FROM persoa_papel)"))
    with op.batch_alter_table("persoa") as batch:
        for columna in _BOOLEANOS:
            batch.drop_column(columna)
        batch.alter_column("tipo", existing_type=sa.String(10), nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("persoa") as batch:
        for columna in _BOOLEANOS:
            batch.add_column(sa.Column(columna, sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
    conn = op.get_bind()
    for columna, papel in _BOOLEANOS.items():
        conn.execute(sa.text(
            f"UPDATE persoa SET {columna} = 1 WHERE id IN "
            f"(SELECT persoa_id FROM persoa_papel WHERE papel = '{papel}')"))
    with op.batch_alter_table("persoa") as batch:
        for nome, _ in _NOVOS:
            batch.drop_column(nome)
    op.drop_index(op.f("ix_persoa_papel_persoa_id"), table_name="persoa_papel")
    op.drop_table("persoa_papel")

