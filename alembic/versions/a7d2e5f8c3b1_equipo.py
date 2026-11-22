"""equipo: persoas con conta, funcions e datos de emprego

Revision ID: a7d2e5f8c3b1
Revises: f6a1c4e8b9d3
Create Date: 2026-10-23 13:00:00

Cada membro actual pasa a ser unha persoa do equipo ligada á súa conta.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7d2e5f8c3b1"
down_revision: Union[str, Sequence[str], None] = "f6a1c4e8b9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("persoa") as batch:
        batch.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("e_titular", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column("e_traballador", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("telefono", sa.String(30), nullable=True))
        batch.add_column(sa.Column("email", sa.String(255), nullable=True))
        batch.add_column(sa.Column("vinculo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("horas_ano", sa.Float(), nullable=True))
        batch.add_column(sa.Column("formacion_agraria", sa.String(200), nullable=True))
        batch.add_column(sa.Column("xenero", sa.String(10), nullable=True))
        batch.add_column(sa.Column("data_nacemento", sa.Date(), nullable=True))
        batch.add_column(
            sa.Column("discapacidade", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.create_foreign_key("fk_persoa_usuario", "usuario", ["usuario_id"], ["id"])
    op.execute(
        "INSERT INTO persoa (horta_id, nome, usuario_id, email, e_aplicador, e_asesor, activa, "
        "e_titular, e_traballador, discapacidade) "
        "SELECT m.horta_id, u.nome, u.id, u.email, 0, 0, 1, 0, 0, 0 "
        "FROM horta_membro m JOIN usuario u ON u.id = m.usuario_id "
        "WHERE NOT EXISTS (SELECT 1 FROM persoa p "
        "WHERE p.horta_id = m.horta_id AND p.usuario_id = m.usuario_id)"
    )


def downgrade() -> None:
    op.execute("DELETE FROM persoa WHERE usuario_id IS NOT NULL AND e_aplicador = 0 "
               "AND e_asesor = 0")
    with op.batch_alter_table("persoa") as batch:
        batch.drop_constraint("fk_persoa_usuario", type_="foreignkey")
        for columna in ("discapacidade", "data_nacemento", "xenero", "formacion_agraria",
                        "horas_ano", "vinculo", "email", "telefono", "e_traballador",
                        "e_titular", "usuario_id"):
            batch.drop_column(columna)
