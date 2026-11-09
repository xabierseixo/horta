"""usuario: engadir columna idioma

Revision ID: e9f0a1b2c3d4
Revises: d8e9f0a1b2c3
Create Date: 2026-11-09 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e9f0a1b2c3d4"
down_revision: Union[str, Sequence[str], None] = "d8e9f0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("usuario") as batch:
        batch.add_column(
            sa.Column("idioma", sa.String(length=10), nullable=False, server_default="gl")
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("usuario") as batch:
        batch.drop_column("idioma")
