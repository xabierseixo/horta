"""explotacion titular e codigos

Revision ID: c3a9e1f0b7d2
Revises: f752d1bd2c5d
Create Date: 2026-10-22 23:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3a9e1f0b7d2"
down_revision: Union[str, Sequence[str], None] = "f752d1bd2c5d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("horta") as batch:
        batch.add_column(sa.Column("titular_nome", sa.String(length=200), nullable=True))
        batch.add_column(sa.Column("titular_nif", sa.String(length=9), nullable=True))
        batch.add_column(sa.Column("codigo_reaga", sa.String(length=14), nullable=True))
        batch.add_column(sa.Column("codigo_rega", sa.String(length=14), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("horta") as batch:
        batch.drop_column("codigo_rega")
        batch.drop_column("codigo_reaga")
        batch.drop_column("titular_nif")
        batch.drop_column("titular_nome")
