"""plan de empresa: datos do Anexo III, ofertas (Anexo VI-A) e partidas do Anexo V

Revision ID: 8cc02f1fdc99
Revises: 38d8d715b590
Create Date: 2026-10-30 21:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8cc02f1fdc99'
down_revision: Union[str, Sequence[str], None] = '38d8d715b590'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TEXTOS = ('situacion_partida', 'metodoloxia', 'mercado')
_MARCAS = ('participada', 'ofertas_autenticas', 'sen_vinculo_promotor',
           'sen_vinculo_entre_provedores')


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('plan_empresa') as batch:
        batch.add_column(sa.Column('tipoloxia', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('expediente', sa.String(length=30), nullable=True))
        batch.add_column(sa.Column('anualidade', sa.Integer(), nullable=True))
        batch.add_column(sa.Column('submedida', sa.String(length=20), nullable=True))
        batch.add_column(sa.Column('gdr', sa.String(length=100), nullable=True))
        batch.add_column(sa.Column('traballadores', sa.Float(), nullable=True))
        batch.add_column(sa.Column('facturacion', sa.Float(), nullable=True))
        batch.add_column(sa.Column('balance', sa.Float(), nullable=True))
        batch.add_column(sa.Column('iva_recuperable', sa.Boolean(), nullable=False,
                                   server_default=sa.true()))
        for campo in _MARCAS:
            batch.add_column(sa.Column(campo, sa.Boolean(), nullable=False,
                                       server_default=sa.false()))
        for campo in _TEXTOS:
            batch.add_column(sa.Column(campo, sa.Text(), nullable=True))
    with op.batch_alter_table('plan_ano') as batch:
        batch.add_column(sa.Column('ingresos_financeiros', sa.Float(), nullable=False,
                                   server_default='0'))
    with op.batch_alter_table('plan_investimento') as batch:
        batch.add_column(sa.Column('motivo_sen_ofertas', sa.Text(), nullable=True))
        batch.drop_column('ofertas')
    # Partidas do Anexo V tal como están no DOG: 4 estudos, 5 constitución, 6 outros
    for vella, nova in (('4', 'x'), ('5', '4'), ('6', '5'), ('x', '6')):
        op.execute(sa.text("UPDATE plan_investimento SET partida = :nova "
                           "WHERE partida = :vella").bindparams(vella=vella, nova=nova))
    op.create_table(
        'plan_oferta',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('investimento_id', sa.Integer(), nullable=False),
        sa.Column('provedor_id', sa.Integer(), nullable=False),
        sa.Column('importe_sen_iva', sa.Float(), nullable=False),
        sa.Column('elixida', sa.Boolean(), nullable=False),
        sa.Column('criterio', sa.String(length=200), nullable=True),
        sa.Column('xustificacion', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['investimento_id'], ['plan_investimento.id']),
        sa.ForeignKeyConstraint(['provedor_id'], ['persoa.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_plan_oferta_investimento_id', 'plan_oferta', ['investimento_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_plan_oferta_investimento_id', table_name='plan_oferta')
    op.drop_table('plan_oferta')
    for vella, nova in (('6', 'x'), ('5', '6'), ('4', '5'), ('x', '4')):
        op.execute(sa.text("UPDATE plan_investimento SET partida = :nova "
                           "WHERE partida = :vella").bindparams(vella=vella, nova=nova))
    with op.batch_alter_table('plan_investimento') as batch:
        batch.add_column(sa.Column('ofertas', sa.Integer(), nullable=False,
                                   server_default='0'))
        batch.drop_column('motivo_sen_ofertas')
    with op.batch_alter_table('plan_ano') as batch:
        batch.drop_column('ingresos_financeiros')
    with op.batch_alter_table('plan_empresa') as batch:
        for campo in (*_TEXTOS, *_MARCAS, 'iva_recuperable', 'balance', 'facturacion',
                      'traballadores', 'gdr', 'submedida', 'anualidade', 'expediente',
                      'tipoloxia'):
            batch.drop_column(campo)
