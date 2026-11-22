"""varias leiras nun traballo: labor, rega e abonado gardan as súas leiras nunha táboa filla

Revision ID: a3d5f7b9c1e8
Revises: f2c4e6a8b0d5
Create Date: 2026-10-28 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3d5f7b9c1e8'
down_revision: Union[str, Sequence[str], None] = 'f2c4e6a8b0d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TRABALLOS = ("labor", "rega", "abonado")


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    for taboa in _TRABALLOS:
        filla = f"{taboa}_cultivo"
        op.create_table(
            filla,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column(f"{taboa}_id", sa.Integer(), nullable=False),
            sa.Column("cultivo_id", sa.Integer(), nullable=False),
            sa.Column("superficie_ha", sa.Float(), nullable=True),
            sa.ForeignKeyConstraint([f"{taboa}_id"], [f"{taboa}.id"]),
            sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f(f"ix_{filla}_{taboa}_id"), filla, [f"{taboa}_id"])
        op.create_index(op.f(f"ix_{filla}_cultivo_id"), filla, ["cultivo_id"])
        # Cada traballo de agora tiña un cultivo: pasa a ser a súa única leira
        conn.execute(sa.text(
            f"INSERT INTO {filla} ({taboa}_id, cultivo_id, superficie_ha) "
            f"SELECT id, cultivo_id, superficie_ha FROM {taboa}"))
        with op.batch_alter_table(taboa) as batch:
            batch.drop_index(f"ix_{taboa}_cultivo_id")
            batch.drop_column("cultivo_id")
            batch.drop_column("superficie_ha")


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    for taboa in _TRABALLOS:
        filla = f"{taboa}_cultivo"
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("cultivo_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("superficie_ha", sa.Float(), nullable=True))
        # Volve a primeira leira de cada traballo (as demais pérdense ao volver atrás)
        conn.execute(sa.text(
            f"UPDATE {taboa} SET (cultivo_id, superficie_ha) = (SELECT cultivo_id, "
            f"superficie_ha FROM {filla} WHERE {filla}.{taboa}_id = {taboa}.id "
            f"ORDER BY {filla}.id LIMIT 1)"))
        with op.batch_alter_table(taboa) as batch:
            batch.alter_column("cultivo_id", existing_type=sa.Integer(), nullable=False)
            batch.create_foreign_key(f"fk_{taboa}_cultivo_id", "cultivo", ["cultivo_id"], ["id"])
            batch.create_index(f"ix_{taboa}_cultivo_id", ["cultivo_id"])
        op.drop_index(op.f(f"ix_{filla}_cultivo_id"), table_name=filla)
        op.drop_index(op.f(f"ix_{filla}_{taboa}_id"), table_name=filla)
        op.drop_table(filla)
