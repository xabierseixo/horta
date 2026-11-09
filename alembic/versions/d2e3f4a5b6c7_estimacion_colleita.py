"""estimacion da colleita

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "estimacion_colleita",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("metodo", sa.String(length=20), nullable=False),
        sa.Column("plantas_ha", sa.Float(), nullable=True),
        sa.Column("unidades_planta", sa.Float(), nullable=True),
        sa.Column("peso_unidade_g", sa.Float(), nullable=True),
        sa.Column("kg_ha", sa.Float(), nullable=False),
        sa.Column("notas", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_estimacion_colleita_cultivo_id"),
        "estimacion_colleita",
        ["cultivo_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_estimacion_colleita_cultivo_id"),
        table_name="estimacion_colleita",
    )
    op.drop_table("estimacion_colleita")
