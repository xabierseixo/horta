"""coidados: o provedor do medicamento, o veterinario e quen visita son persoas

Revision ID: c9f1b3d5e7a2
Revises: b8e0a2c4d6f1
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'c9f1b3d5e7a2'
down_revision: Union[str, Sequence[str], None] = 'b8e0a2c4d6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_CAMPOS = (("provedor", "provedor_id", "provedor"), ("veterinario", "veterinario_id",
                                                       "veterinario"),
           ("visitante", "visitante_id", None))


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("coidado_animal") as batch:
        for _, columna, _ in _CAMPOS:
            batch.add_column(sa.Column(columna, sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_coidado_animal_{columna}", "persoa", [columna],
                                     ["id"])
    for texto, columna, papel in _CAMPOS:
        # Quen visita non ten un papel fixo: queda como contacto sen papel
        pasar_a_persoas(op.get_bind(), "coidado_animal", columna, papel,
                        f"SELECT id, horta_id, {texto} FROM coidado_animal",
                        nome=lambda f, t=texto: f[t])
    with op.batch_alter_table("coidado_animal") as batch:
        for texto, _, _ in _CAMPOS:
            batch.drop_column(texto)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("coidado_animal") as batch:
        batch.add_column(sa.Column("provedor", sa.String(300), nullable=True))
        batch.add_column(sa.Column("veterinario", sa.String(200), nullable=True))
        batch.add_column(sa.Column("visitante", sa.String(200), nullable=True))
    for texto, columna, _ in _CAMPOS:
        op.get_bind().execute(sa.text(
            f"UPDATE coidado_animal SET {texto} = (SELECT nome FROM persoa "
            f"WHERE persoa.id = coidado_animal.{columna})"))
    with op.batch_alter_table("coidado_animal") as batch:
        for _, columna, _ in _CAMPOS:
            batch.drop_constraint(f"fk_coidado_animal_{columna}", type_="foreignkey")
            batch.drop_column(columna)
