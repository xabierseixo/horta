"""análises: o laboratorio é unha persoa (entidade co seu NIF)

Revision ID: d0a2c4e6f8b3
Revises: c9f1b3d5e7a2
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'd0a2c4e6f8b3'
down_revision: Union[str, Sequence[str], None] = 'c9f1b3d5e7a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("analise") as batch:
        batch.add_column(sa.Column("laboratorio_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_analise_laboratorio_id", "persoa", ["laboratorio_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "analise", "laboratorio_id", "laboratorio",
        "SELECT id, horta_id, laboratorio, laboratorio_nif FROM analise",
        nome=lambda f: primeiro(f["laboratorio"], f["laboratorio_nif"]),
        datos=lambda f: {"nif": f["laboratorio_nif"], "tipo": "entidade"})
    with op.batch_alter_table("analise") as batch:
        batch.drop_column("laboratorio")
        batch.drop_column("laboratorio_nif")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("analise") as batch:
        batch.add_column(sa.Column("laboratorio", sa.String(150), nullable=True))
        batch.add_column(sa.Column("laboratorio_nif", sa.String(9), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE analise SET (laboratorio, laboratorio_nif) = (SELECT nome, nif FROM persoa "
        "WHERE persoa.id = analise.laboratorio_id)"))
    with op.batch_alter_table("analise") as batch:
        batch.drop_constraint("fk_analise_laboratorio_id", type_="foreignkey")
        batch.drop_column("laboratorio_id")
