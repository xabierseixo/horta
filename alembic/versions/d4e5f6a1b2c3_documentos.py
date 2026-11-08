"""documentos e certificacións

Revision ID: d4e5f6a1b2c3
Revises: e3f8a1b2c4d5
Create Date: 2026-11-08 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a1b2c3'
down_revision: Union[str, Sequence[str], None] = 'e3f8a1b2c4d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "documento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("emisor", sa.String(length=200), nullable=True),
        sa.Column("numero", sa.String(length=100), nullable=True),
        sa.Column("data_emision", sa.Date(), nullable=True),
        sa.Column("data_caducidade", sa.Date(), nullable=True),
        sa.Column("que", sa.String(length=30), nullable=True),
        sa.Column("ref_id", sa.Integer(), nullable=True),
        sa.Column("ficheiro", sa.String(length=60), nullable=True),
        sa.Column("nome_orixinal", sa.String(length=200), nullable=True),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documento_horta_id"), "documento", ["horta_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_documento_horta_id"), table_name="documento")
    op.drop_table("documento")
