"""rgpd: configuracion_legal e politica de privacidade en usuario

Revision ID: e3f8a1b2c4d5
Revises: c2784bdf2b44
Create Date: 2026-11-08 16:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3f8a1b2c4d5'
down_revision: Union[str, Sequence[str], None] = 'c2784bdf2b44'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'configuracion_legal',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=True),
        sa.Column('nif', sa.String(length=50), nullable=True),
        sa.Column('enderezo', sa.String(length=200), nullable=True),
        sa.Column('correo', sa.String(length=255), nullable=True),
        sa.Column('dpd', sa.String(length=255), nullable=True),
        sa.Column('localizacion', sa.Text(), nullable=True),
        sa.Column('actualizado_en', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('usuario') as batch:
        batch.add_column(sa.Column('politica_version', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('politica_aceptada_en', sa.DateTime(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('usuario') as batch:
        batch.drop_column('politica_aceptada_en')
        batch.drop_column('politica_version')
    op.drop_table('configuracion_legal')
