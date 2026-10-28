"""parte común no tratamento: as observacións son as notas; quen o apuntou

Revision ID: a1d3f5b7c9e4
Revises: f0c2e4a6b8d3
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d3f5b7c9e4'
down_revision: Union[str, Sequence[str], None] = 'f0c2e4a6b8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tratamento_fito") as batch:
        batch.alter_column("observacions", new_column_name="notas")
        batch.add_column(sa.Column("creado_por", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tratamento_fito_creado_por", "usuario",
                                 ["creado_por"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tratamento_fito") as batch:
        batch.drop_constraint("fk_tratamento_fito_creado_por", type_="foreignkey")
        batch.drop_column("creado_por")
        batch.alter_column("notas", new_column_name="observacions")
