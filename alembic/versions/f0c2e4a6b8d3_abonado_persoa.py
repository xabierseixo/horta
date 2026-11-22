"""parte común: quen aplicou o abono chámase persoa_id, como nos outros traballos

Revision ID: f0c2e4a6b8d3
Revises: e9b1d3f5a7c2
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0c2e4a6b8d3'
down_revision: Union[str, Sequence[str], None] = 'e9b1d3f5a7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.alter_column("aplicador_persoa_id", new_column_name="persoa_id")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.alter_column("persoa_id", new_column_name="aplicador_persoa_id")
