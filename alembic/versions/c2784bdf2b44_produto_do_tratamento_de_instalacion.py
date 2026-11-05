"""produto do tratamento de instalacion

Revision ID: c2784bdf2b44
Revises: 8cc02f1fdc99
Create Date: 2026-11-05 15:54:03.730611

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2784bdf2b44'
down_revision: Union[str, Sequence[str], None] = '8cc02f1fdc99'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """O produto e a compra dun tratamento de instalación, para descontalo (Z8)."""
    with op.batch_alter_table("tratamento_instalacion") as batch:
        batch.add_column(sa.Column("produto_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("entrada_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tratamento_instalacion_produto", "produto",
                                 ["produto_id"], ["id"])
        batch.create_foreign_key("fk_tratamento_instalacion_entrada", "entrada_produto",
                                 ["entrada_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("tratamento_instalacion") as batch:
        batch.drop_constraint("fk_tratamento_instalacion_entrada", type_="foreignkey")
        batch.drop_constraint("fk_tratamento_instalacion_produto", type_="foreignkey")
        batch.drop_column("entrada_id")
        batch.drop_column("produto_id")
