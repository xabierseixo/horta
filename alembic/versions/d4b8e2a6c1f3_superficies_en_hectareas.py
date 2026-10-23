"""superficies en hectareas

Revision ID: d4b8e2a6c1f3
Revises: c3a9e1f0b7d2
Create Date: 2026-10-23 10:00:00

Parcelas e fertilizacións gardaban a superficie en m²; o CUE pide hectáreas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "d4b8e2a6c1f3"
down_revision: Union[str, Sequence[str], None] = "c3a9e1f0b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE parcela SET superficie = superficie / 10000.0 WHERE superficie IS NOT NULL")
    op.execute(
        "UPDATE fertilizacion SET superficie = superficie / 10000.0 WHERE superficie IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("UPDATE parcela SET superficie = superficie * 10000.0 WHERE superficie IS NOT NULL")
    op.execute(
        "UPDATE fertilizacion SET superficie = superficie * 10000.0 WHERE superficie IS NOT NULL"
    )
