"""envíos ao CUE da Xunta e estado de cada actividade

Revision ID: d16e0facc85c
Revises: 5521d07a1942
Create Date: 2026-10-30 14:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd16e0facc85c'
down_revision: Union[str, Sequence[str], None] = '5521d07a1942'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('envio_cue',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('horta_id', sa.Integer(), nullable=False),
    sa.Column('usuario_id', sa.Integer(), nullable=False),
    sa.Column('enviado', sa.DateTime(), nullable=False),
    sa.Column('desde', sa.Date(), nullable=False),
    sa.Column('ata', sa.Date(), nullable=False),
    sa.Column('actividades', sa.Integer(), nullable=False),
    sa.Column('peticion', sa.BigInteger(), nullable=True),
    sa.Column('resultado', sa.String(length=20), nullable=False),
    sa.Column('mensaxes', sa.Text(), nullable=True),
    sa.Column('comprobado', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['horta_id'], ['horta.id'], ),
    sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_envio_cue_horta_id'), 'envio_cue', ['horta_id'], unique=False)
    op.create_table('rexistro_cue',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('horta_id', sa.Integer(), nullable=False),
    sa.Column('bloque', sa.String(length=40), nullable=False),
    sa.Column('id_ajena', sa.BigInteger(), nullable=False),
    sa.Column('orixe_tipo', sa.String(length=30), nullable=False),
    sa.Column('orixe_id', sa.Integer(), nullable=True),
    sa.Column('data', sa.Date(), nullable=True),
    sa.Column('pegada', sa.String(length=64), nullable=False),
    sa.Column('datos', sa.Text(), nullable=False),
    sa.Column('borrado', sa.Boolean(), nullable=False),
    sa.Column('estado', sa.String(length=20), nullable=False),
    sa.Column('mensaxe', sa.String(length=500), nullable=True),
    sa.Column('id_cuaderno', sa.BigInteger(), nullable=True),
    sa.Column('envio_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['envio_id'], ['envio_cue.id'], ),
    sa.ForeignKeyConstraint(['horta_id'], ['horta.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('horta_id', 'bloque', 'id_ajena')
    )
    op.create_index(op.f('ix_rexistro_cue_horta_id'), 'rexistro_cue', ['horta_id'],
                    unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_rexistro_cue_horta_id'), table_name='rexistro_cue')
    op.drop_table('rexistro_cue')
    op.drop_index(op.f('ix_envio_cue_horta_id'), table_name='envio_cue')
    op.drop_table('envio_cue')
