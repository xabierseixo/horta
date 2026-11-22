"""fotos dos traballos, parcelas, animais e lotes

Revision ID: c2a4e6b8d0f1
Revises: b1f3d5e7a9c2
Create Date: 2026-10-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a4e6b8d0f1'
down_revision: Union[str, Sequence[str], None] = 'b1f3d5e7a9c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "foto",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("que", sa.String(length=30), nullable=False),
        sa.Column("ref_id", sa.Integer(), nullable=False),
        sa.Column("ficheiro", sa.String(length=60), nullable=False),
        sa.Column("nome_orixinal", sa.String(length=200), nullable=True),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("nota", sa.String(length=300), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_foto_horta_id"), "foto", ["horta_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_foto_horta_id"), table_name="foto")
    op.drop_table("foto")
