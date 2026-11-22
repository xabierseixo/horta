"""o estado do cultivo calcúlase dos seus traballos (services.cultivos.estado_cultivo)

Revision ID: b2e4a6c8d0f5
Revises: a1d3f5b7c9e4
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e4a6c8d0f5'
down_revision: Union[str, Sequence[str], None] = 'a1d3f5b7c9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("estado")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("estado", sa.String(length=50), nullable=False,
                                   server_default="planificado"))
