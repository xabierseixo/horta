"""os cartos: cobros e pagos, prezo dos animais, custo da hora e outros gastos e ingresos

Revision ID: b1f3d5e7a9c2
Revises: a0e2c4f6b8d3
Create Date: 2026-10-29 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f3d5e7a9c2'
down_revision: Union[str, Sequence[str], None] = 'a0e2c4f6b8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "apunte_cartos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("categoria", sa.String(length=20), nullable=False),
        sa.Column("concepto", sa.String(length=200), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("importe", sa.Float(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("albaran_factura", sa.String(length=60), nullable=True),
        sa.Column("data_pago", sa.Date(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_apunte_cartos_horta_id"), "apunte_cartos", ["horta_id"])
    for taboa in ("lote_saida", "entrada_produto"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("data_pago", sa.Date(), nullable=True))
    with op.batch_alter_table("movemento_animal") as batch:
        batch.add_column(sa.Column("importe", sa.Float(), nullable=True))
        batch.add_column(sa.Column("data_pago", sa.Date(), nullable=True))
    for taboa in ("persoa", "maquina"):
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("custo_hora", sa.Float(), nullable=True))
    # Antes non había onde dicir que unha venda ou compra estaba pendente: o que ten prezo
    # márcase cobrado ou pagado na súa data (pódese cambiar despois)
    op.execute("UPDATE lote_saida SET data_pago = data_fin "
               "WHERE importe IS NOT NULL AND tipo = 'venda'")
    op.execute("UPDATE entrada_produto SET data_pago = data WHERE importe IS NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in ("persoa", "maquina"):
        with op.batch_alter_table(taboa) as batch:
            batch.drop_column("custo_hora")
    with op.batch_alter_table("movemento_animal") as batch:
        batch.drop_column("data_pago")
        batch.drop_column("importe")
    for taboa in ("lote_saida", "entrada_produto"):
        with op.batch_alter_table(taboa) as batch:
            batch.drop_column("data_pago")
    op.drop_index(op.f("ix_apunte_cartos_horta_id"), table_name="apunte_cartos")
    op.drop_table("apunte_cartos")
