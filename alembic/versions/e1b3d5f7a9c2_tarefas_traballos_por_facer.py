"""tarefas = traballos por facer: tipo, quen, horas e o traballo apuntado

Revision ID: e1b3d5f7a9c2
Revises: d0a2c4e6f8b1
Create Date: 2026-10-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b3d5f7a9c2'
down_revision: Union[str, Sequence[str], None] = 'd0a2c4e6f8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.add_column(sa.Column("tipo", sa.String(length=30), nullable=True))
        batch.add_column(sa.Column("persoa_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tarefa_persoa_id", "persoa", ["persoa_id"], ["id"])
        batch.add_column(sa.Column("horas", sa.Float(), nullable=True))
        batch.add_column(sa.Column("traballo_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.drop_column("traballo_id")
        batch.drop_column("horas")
        batch.drop_constraint("fk_tarefa_persoa_id", type_="foreignkey")
        batch.drop_column("persoa_id")
        batch.drop_column("tipo")
