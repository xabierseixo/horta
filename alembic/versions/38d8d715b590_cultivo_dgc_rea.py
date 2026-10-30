"""cultivo: DGC e cultivo do REA da Xunta

Revision ID: 38d8d715b590
Revises: d16e0facc85c
Create Date: 2026-10-30 15:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '38d8d715b590'
down_revision: Union[str, Sequence[str], None] = 'd16e0facc85c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('cultivo') as batch:
        batch.add_column(sa.Column('codigo_dgc', sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column('codigo_cultivo_rea', sa.BigInteger(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('cultivo') as batch:
        batch.drop_column('codigo_cultivo_rea')
        batch.drop_column('codigo_dgc')
