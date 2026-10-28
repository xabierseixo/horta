"""pastoreo: o gando doutra persoa leva a súa explotación (persoa co REGA)

Revision ID: f6c8e0a2b4d9
Revises: e5b7d9f1a3c8
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas


# revision identifiers, used by Alembic.
revision: str = 'f6c8e0a2b4d9'
down_revision: Union[str, Sequence[str], None] = 'e5b7d9f1a3c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.add_column(sa.Column("propietario_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_pastoreo_animal_propietario_id", "persoa",
                                 ["propietario_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "pastoreo_animal", "propietario_id", "explotacion",
        "SELECT pa.id, p.horta_id, pa.rega FROM pastoreo_animal pa "
        "JOIN pastoreo p ON p.id = pa.pastoreo_id",
        nome=lambda f: f["rega"] and f"Explotación {f['rega']}",
        datos=lambda f: {"rega": f["rega"]})
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.drop_column("rega")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.add_column(sa.Column("rega", sa.String(14), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE pastoreo_animal SET rega = (SELECT rega FROM persoa "
        "WHERE persoa.id = pastoreo_animal.propietario_id)"))
    with op.batch_alter_table("pastoreo_animal") as batch:
        batch.drop_constraint("fk_pastoreo_animal_propietario_id", type_="foreignkey")
        batch.drop_column("propietario_id")
