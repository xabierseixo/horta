"""produción dos animais

Revision ID: b5d7f9a1c3e6
Revises: a4b6d8f0c2e5
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5d7f9a1c3e6'
down_revision: Union[str, Sequence[str], None] = 'a4b6d8f0c2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "producion_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=False),
        sa.Column("produto", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("retirada", sa.Float(), nullable=True),
        sa.Column("lote", sa.String(length=40), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_producion_animal_horta_id", "producion_animal", ["horta_id"])
    op.create_index("ix_producion_animal_animal_id", "producion_animal", ["animal_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_producion_animal_animal_id", table_name="producion_animal")
    op.drop_index("ix_producion_animal_horta_id", table_name="producion_animal")
    op.drop_table("producion_animal")
