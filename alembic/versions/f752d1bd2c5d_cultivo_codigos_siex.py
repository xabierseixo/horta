"""cultivo codigos siex

Revision ID: f752d1bd2c5d
Revises: b85c3390befb
Create Date: 2026-10-22 22:13:36.623579

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f752d1bd2c5d'
down_revision: Union[str, Sequence[str], None] = 'b85c3390befb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("cultivo_siex_codigo", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("variedade_siex_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("variedade_local_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_cultivo_cultivo_siex", "cultivo_siex", ["cultivo_siex_codigo"], ["codigo"]
        )
        batch.create_foreign_key(
            "fk_cultivo_variedade_siex", "variedade_siex", ["variedade_siex_id"], ["id"]
        )
        batch.create_foreign_key(
            "fk_cultivo_variedade_local", "variedade_local", ["variedade_local_id"], ["id"]
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_constraint("fk_cultivo_variedade_local", type_="foreignkey")
        batch.drop_constraint("fk_cultivo_variedade_siex", type_="foreignkey")
        batch.drop_constraint("fk_cultivo_cultivo_siex", type_="foreignkey")
        batch.drop_column("variedade_local_id")
        batch.drop_column("variedade_siex_id")
        batch.drop_column("cultivo_siex_codigo")
