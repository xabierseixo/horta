"""acceso para inspeccion e auditoria

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-11-09 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "rexistro_acceso",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("data_hora", sa.DateTime(), nullable=False),
        sa.Column("seccion", sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_rexistro_acceso_horta_id"),
        "rexistro_acceso",
        ["horta_id"],
        unique=False,
    )
    with op.batch_alter_table("convite") as batch:
        batch.add_column(sa.Column("acceso_ata", sa.Date(), nullable=True))
        batch.add_column(sa.Column("motivo", sa.String(length=30), nullable=True))
    with op.batch_alter_table("horta_membro") as batch:
        batch.add_column(sa.Column("acceso_ata", sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("horta_membro") as batch:
        batch.drop_column("acceso_ata")
    with op.batch_alter_table("convite") as batch:
        batch.drop_column("motivo")
        batch.drop_column("acceso_ata")
    op.drop_index(
        op.f("ix_rexistro_acceso_horta_id"),
        table_name="rexistro_acceso",
    )
    op.drop_table("rexistro_acceso")
