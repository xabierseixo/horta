"""plan_vendas

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-11-09 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b6c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plan_venda",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("produto", sa.String(length=100), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("canle", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("prezo", sa.Float(), nullable=False),
        sa.Column("custo_unitario", sa.Float(), nullable=True),
        sa.Column("crece_cantidade_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("crece_prezo_pct", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "meses",
            sa.String(length=40),
            nullable=False,
            server_default=sa.text("'1,2,3,4,5,6,7,8,9,10,11,12'"),
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["plan_empresa.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_plan_venda_plan_id"), "plan_venda", ["plan_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_plan_venda_plan_id"), table_name="plan_venda")
    op.drop_table("plan_venda")
