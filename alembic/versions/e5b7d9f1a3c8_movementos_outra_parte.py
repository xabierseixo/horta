"""entradas e saídas de animais: a outra explotación é unha persoa (titular e REGA)

Revision ID: e5b7d9f1a3c8
Revises: d4a6c8e0f2b7
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'e5b7d9f1a3c8'
down_revision: Union[str, Sequence[str], None] = 'd4a6c8e0f2b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("movemento_animal") as batch:
        batch.add_column(sa.Column("outra_parte_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_movemento_animal_outra_parte_id", "persoa",
                                 ["outra_parte_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "movemento_animal", "outra_parte_id", "explotacion",
        "SELECT id, horta_id, titular, rega FROM movemento_animal",
        nome=lambda f: primeiro(f["titular"], f["rega"] and f"Explotación {f['rega']}"),
        datos=lambda f: {"rega": f["rega"]})
    with op.batch_alter_table("movemento_animal") as batch:
        batch.drop_column("titular")
        batch.drop_column("rega")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("movemento_animal") as batch:
        batch.add_column(sa.Column("titular", sa.String(300), nullable=True))
        batch.add_column(sa.Column("rega", sa.String(20), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE movemento_animal SET (titular, rega) = (SELECT nome, rega FROM persoa "
        "WHERE persoa.id = movemento_animal.outra_parte_id)"))
    with op.batch_alter_table("movemento_animal") as batch:
        batch.drop_constraint("fk_movemento_animal_outra_parte_id", type_="foreignkey")
        batch.drop_column("outra_parte_id")
