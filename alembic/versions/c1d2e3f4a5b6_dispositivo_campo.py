"""dispositivo: claves dos móbiles para a app do campo

Revision ID: c1d2e3f4a5b6
Revises: a7b8c9d0e1f2
Create Date: 2026-11-08 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "dispositivo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("creado_en", sa.DateTime(), nullable=False),
        sa.Column("ultimo_uso", sa.DateTime(), nullable=True),
        sa.Column("revogado", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_dispositivo_usuario_id"),
        "dispositivo",
        ["usuario_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dispositivo_token_hash"),
        "dispositivo",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_dispositivo_token_hash"), table_name="dispositivo")
    op.drop_index(op.f("ix_dispositivo_usuario_id"), table_name="dispositivo")
    op.drop_table("dispositivo")
