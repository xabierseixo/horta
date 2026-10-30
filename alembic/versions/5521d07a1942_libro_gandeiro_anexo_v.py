"""libro gandeiro: clasificación e capacidade REGA, titular dos animais e dispositivo

Revision ID: 5521d07a1942
Revises: c2a4e6f8b0d1
Create Date: 2026-10-30 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5521d07a1942'
down_revision: Union[str, Sequence[str], None] = 'c2a4e6f8b0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('horta') as batch:
        batch.add_column(sa.Column('rega_clasificacion', sa.String(length=200), nullable=True))
        batch.add_column(sa.Column('rega_capacidade', sa.String(length=100), nullable=True))
    with op.batch_alter_table('animal') as batch:
        batch.add_column(sa.Column('titular_animais_id', sa.Integer(), nullable=True))
        batch.create_foreign_key('fk_animal_titular_animais', 'persoa',
                                 ['titular_animais_id'], ['id'])
    with op.batch_alter_table('animal_identificado') as batch:
        batch.add_column(sa.Column('dispositivo', sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('animal_identificado') as batch:
        batch.drop_column('dispositivo')
    with op.batch_alter_table('animal') as batch:
        batch.drop_constraint('fk_animal_titular_animais', type_='foreignkey')
        batch.drop_column('titular_animais_id')
    with op.batch_alter_table('horta') as batch:
        batch.drop_column('rega_capacidade')
        batch.drop_column('rega_clasificacion')
