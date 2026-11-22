"""emails en minusculas

Revision ID: e5c9f3b7d2a4
Revises: d4b8e2a6c1f3
Create Date: 2026-10-23 11:00:00

O login compara o email en minúsculas e sen espazos; normalízanse os xa gardados.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "e5c9f3b7d2a4"
down_revision: Union[str, Sequence[str], None] = "d4b8e2a6c1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE usuario SET email = lower(trim(email))")


def downgrade() -> None:
    pass
