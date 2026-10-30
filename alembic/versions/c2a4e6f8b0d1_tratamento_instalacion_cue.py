"""tratamento en instalacións: produto vexetal, instalación e eficacia (CUE)

Revision ID: c2a4e6f8b0d1
Revises: ee20f21b4ca4
Create Date: 2026-10-30 13:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a4e6f8b0d1'
down_revision: Union[str, Sequence[str], None] = 'ee20f21b4ca4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('tratamento_instalacion') as batch:
        batch.add_column(sa.Column('produto_vexetal', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('instalacion_id', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('eficacia', sa.String(length=20), nullable=True))
        batch.create_foreign_key('fk_tratamento_instalacion_instalacion', 'instalacion',
                                 ['instalacion_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('tratamento_instalacion') as batch:
        batch.drop_constraint('fk_tratamento_instalacion_instalacion', type_='foreignkey')
        batch.drop_column('eficacia')
        batch.drop_column('instalacion_id')
        batch.drop_column('produto_vexetal')
