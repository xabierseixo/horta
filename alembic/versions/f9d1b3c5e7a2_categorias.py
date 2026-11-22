"""categorías dos contactos: libres por explotación

Revision ID: f9d1b3c5e7a2
Revises: e8c0a2b4d6f1
Create Date: 2026-10-29 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f9d1b3c5e7a2'
down_revision: Union[str, Sequence[str], None] = 'e8c0a2b4d6f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=60), nullable=False),
        sa.Column("papel", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("horta_id", "nome"),
        sa.UniqueConstraint("horta_id", "papel"),
    )
    op.create_index(op.f("ix_categoria_horta_id"), "categoria", ["horta_id"], unique=False)
    op.create_table(
        "persoa_categoria",
        sa.Column("persoa_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.PrimaryKeyConstraint("persoa_id", "categoria_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("persoa_categoria")
    op.drop_index(op.f("ix_categoria_horta_id"), table_name="categoria")
    op.drop_table("categoria")
