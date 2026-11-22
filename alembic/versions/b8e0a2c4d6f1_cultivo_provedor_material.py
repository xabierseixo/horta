"""cultivo: o provedor da semente ou planta é unha persoa, co seu ROPVEG

Revision ID: b8e0a2c4d6f1
Revises: a7d9f1b3c5e0
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'b8e0a2c4d6f1'
down_revision: Union[str, Sequence[str], None] = 'a7d9f1b3c5e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("provedor_material_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_cultivo_provedor_material_id", "persoa", ["provedor_material_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "cultivo", "provedor_material_id", "provedor",
        "SELECT c.id, p.horta_id, c.provedor_material, c.ropveg FROM cultivo c "
        "JOIN parcela p ON p.id = c.parcela_id",
        nome=lambda f: primeiro(f["provedor_material"],
                                f["ropveg"] and f"Provedor (ROPVEG {f['ropveg']})"),
        datos=lambda f: {"ropveg": f["ropveg"]})
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("provedor_material")
        batch.drop_column("ropveg")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("provedor_material", sa.String(200), nullable=True))
        batch.add_column(sa.Column("ropveg", sa.String(20), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE cultivo SET (provedor_material, ropveg) = (SELECT nome, ropveg FROM persoa "
        "WHERE persoa.id = cultivo.provedor_material_id)"))
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_constraint("fk_cultivo_provedor_material_id", type_="foreignkey")
        batch.drop_column("provedor_material_id")
