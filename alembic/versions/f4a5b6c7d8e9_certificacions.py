"""certificacions e autoavaliacion (tarefa 182c)

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-11-09 04:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f4a5b6c7d8e9'
down_revision: Union[str, Sequence[str], None] = 'e3f4a5b6c7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'certificacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('horta_id', sa.Integer(), nullable=False),
        sa.Column('esquema', sa.String(length=30), nullable=False),
        sa.Column('nome', sa.String(length=120), nullable=True),
        sa.Column('numero', sa.String(length=40), nullable=True),
        sa.Column('entidade', sa.String(length=120), nullable=True),
        sa.Column('data_inicio', sa.Date(), nullable=True),
        sa.Column('data_fin', sa.Date(), nullable=True),
        sa.Column('documento_id', sa.Integer(), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['documento_id'], ['documento.id']),
        sa.ForeignKeyConstraint(['horta_id'], ['horta.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_certificacion_horta_id', 'certificacion', ['horta_id'])

    op.create_table(
        'punto_autoavaliacion',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('certificacion_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.Date(), nullable=False),
        sa.Column('punto', sa.String(length=30), nullable=False),
        sa.Column('resultado', sa.String(length=12), nullable=False),
        sa.Column('evidencia', sa.String(length=500), nullable=True),
        sa.Column('documento_id', sa.Integer(), nullable=True),
        sa.Column('accion_correctora', sa.String(length=500), nullable=True),
        sa.Column('data_correccion', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['certificacion_id'], ['certificacion.id']),
        sa.ForeignKeyConstraint(['documento_id'], ['documento.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_punto_autoavaliacion_certificacion_id',
        'punto_autoavaliacion',
        ['certificacion_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        'ix_punto_autoavaliacion_certificacion_id',
        table_name='punto_autoavaliacion',
    )
    op.drop_table('punto_autoavaliacion')
    op.drop_index('ix_certificacion_horta_id', table_name='certificacion')
    op.drop_table('certificacion')
