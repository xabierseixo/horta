"""Plan memoria completa (tarefa 184a).

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-11-09
"""

from alembic import op
import sqlalchemy as sa


revision = "b6c7d8e9f0a1"
down_revision = "a5b6c7d8e9f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("plan_empresa") as batch_op:
        batch_op.add_column(sa.Column("dafo_debilidades", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("dafo_ameazas", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("dafo_fortalezas", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("dafo_oportunidades", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("clientela", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("competencia", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("mk_produto", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("mk_prezo", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("mk_canles", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("mk_comunicacion", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("argumentos", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("organizacion", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("riscos", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("permisos", sa.Text(), nullable=True))

    op.create_table(
        "plan_actividade",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("mes_inicio", sa.Integer(), nullable=False),
        sa.Column("mes_fin", sa.Integer(), nullable=False),
        sa.Column("actividade", sa.String(length=200), nullable=False),
        sa.Column("responsable", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_empresa.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plan_actividade_plan_id", "plan_actividade", ["plan_id"], unique=False
    )

    op.create_table(
        "plan_obxectivo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("obxectivo", sa.String(length=200), nullable=False),
        sa.Column("indicador", sa.String(length=200), nullable=False),
        sa.Column("meta", sa.String(length=100), nullable=True),
        sa.Column("prazo", sa.String(length=60), nullable=True),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_empresa.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_plan_obxectivo_plan_id", "plan_obxectivo", ["plan_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_plan_obxectivo_plan_id", table_name="plan_obxectivo")
    op.drop_table("plan_obxectivo")
    op.drop_index("ix_plan_actividade_plan_id", table_name="plan_actividade")
    op.drop_table("plan_actividade")

    with op.batch_alter_table("plan_empresa") as batch_op:
        batch_op.drop_column("permisos")
        batch_op.drop_column("riscos")
        batch_op.drop_column("organizacion")
        batch_op.drop_column("argumentos")
        batch_op.drop_column("mk_comunicacion")
        batch_op.drop_column("mk_canles")
        batch_op.drop_column("mk_prezo")
        batch_op.drop_column("mk_produto")
        batch_op.drop_column("competencia")
        batch_op.drop_column("clientela")
        batch_op.drop_column("dafo_oportunidades")
        batch_op.drop_column("dafo_fortalezas")
        batch_op.drop_column("dafo_ameazas")
        batch_op.drop_column("dafo_debilidades")
