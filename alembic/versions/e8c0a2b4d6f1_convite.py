"""convite: ligazón para entrar nunha explotación

Revision ID: e8c0a2b4d6f1
Revises: d7b9f1a3c5e8
Create Date: 2026-10-29 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8c0a2b4d6f1'
down_revision: Union[str, Sequence[str], None] = 'd7b9f1a3c5e8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "convite",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=False),
        sa.Column("rol", sa.Enum("ADMIN", "EDITOR", "LECTOR", name="rolhorta"), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=False),
        sa.Column("caduca", sa.DateTime(), nullable=False),
        sa.Column("usado", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_convite_horta_id"), "convite", ["horta_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_convite_horta_id"), table_name="convite")
    op.drop_table("convite")
