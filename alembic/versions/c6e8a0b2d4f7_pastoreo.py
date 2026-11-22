"""pastoreo

Revision ID: c6e8a0b2d4f7
Revises: b5d7f9a1c3e6
Create Date: 2026-10-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6e8a0b2d4f7'
down_revision: Union[str, Sequence[str], None] = 'b5d7f9a1c3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pastoreo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_pastoreo_horta_id", "pastoreo", ["horta_id"])
    op.create_table(
        "pastoreo_leira",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pastoreo_id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("superficie_ha", sa.Float(), nullable=True),
        sa.Column("tipo_cobertura", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["pastoreo_id"], ["pastoreo.id"]),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pastoreo_leira_pastoreo_id", "pastoreo_leira", ["pastoreo_id"])
    op.create_index("ix_pastoreo_leira_cultivo_id", "pastoreo_leira", ["cultivo_id"])
    op.create_table(
        "pastoreo_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pastoreo_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=True),
        sa.Column("rega", sa.String(length=14), nullable=True),
        sa.Column("especie_codigo", sa.String(length=20), nullable=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["pastoreo_id"], ["pastoreo.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pastoreo_animal_pastoreo_id", "pastoreo_animal", ["pastoreo_id"])
    op.create_index("ix_pastoreo_animal_animal_id", "pastoreo_animal", ["animal_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_pastoreo_animal_animal_id", table_name="pastoreo_animal")
    op.drop_index("ix_pastoreo_animal_pastoreo_id", table_name="pastoreo_animal")
    op.drop_table("pastoreo_animal")
    op.drop_index("ix_pastoreo_leira_cultivo_id", table_name="pastoreo_leira")
    op.drop_index("ix_pastoreo_leira_pastoreo_id", table_name="pastoreo_leira")
    op.drop_table("pastoreo_leira")
    op.drop_index("ix_pastoreo_horta_id", table_name="pastoreo")
    op.drop_table("pastoreo")
