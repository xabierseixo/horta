"""parcelas: quen arrenda ou cede a parcela é unha persoa (co seu NIF)

Revision ID: e1b3d5f7a9c4
Revises: d0a2c4e6f8b3
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'e1b3d5f7a9c4'
down_revision: Union[str, Sequence[str], None] = 'd0a2c4e6f8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("arrendador_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_parcela_arrendador_id", "persoa", ["arrendador_id"], ["id"])
    # O REA só pide o NIF de quen arrenda ou cede (sen papel fixo): o NIF fai de nome
    pasar_a_persoas(
        op.get_bind(), "parcela", "arrendador_id", None,
        "SELECT id, horta_id, nif_arrendador FROM parcela",
        nome=lambda f: f["nif_arrendador"] and f"Arrendador {f['nif_arrendador']}",
        datos=lambda f: {"nif": f["nif_arrendador"]})
    with op.batch_alter_table("parcela") as batch:
        batch.drop_column("nif_arrendador")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("nif_arrendador", sa.String(9), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE parcela SET nif_arrendador = (SELECT nif FROM persoa "
        "WHERE persoa.id = parcela.arrendador_id)"))
    with op.batch_alter_table("parcela") as batch:
        batch.drop_constraint("fk_parcela_arrendador_id", type_="foreignkey")
        batch.drop_column("arrendador_id")
