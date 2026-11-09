"""sensores, lecturas e resumos diarios

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-11-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sensor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("parcela_id", sa.Integer(), nullable=True),
        sa.Column("cultivo_id", sa.Integer(), nullable=True),
        sa.Column("instalacion_id", sa.Integer(), nullable=True),
        sa.Column("clave_hash", sa.String(length=64), nullable=False),
        sa.Column("campo_payload", sa.String(length=60), nullable=True),
        sa.Column("limiar_min", sa.Float(), nullable=True),
        sa.Column("limiar_max", sa.Float(), nullable=True),
        sa.Column("ultima_lectura_en", sa.DateTime(), nullable=True),
        sa.Column("compactado_ata", sa.Date(), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["instalacion_id"], ["instalacion.id"]),
        sa.ForeignKeyConstraint(["parcela_id"], ["parcela.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sensor_clave_hash"), "sensor", ["clave_hash"], unique=True)
    op.create_index(op.f("ix_sensor_horta_id"), "sensor", ["horta_id"], unique=False)

    op.create_table(
        "lectura_sensor",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("momento", sa.DateTime(), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sensor_id", "momento", name="uq_lectura_sensor_sensor_id_momento"),
    )
    op.create_index(
        op.f("ix_lectura_sensor_momento"), "lectura_sensor", ["momento"], unique=False
    )
    op.create_index(
        op.f("ix_lectura_sensor_sensor_id"), "lectura_sensor", ["sensor_id"], unique=False
    )

    op.create_table(
        "lectura_diaria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("minimo", sa.Float(), nullable=False),
        sa.Column("maximo", sa.Float(), nullable=False),
        sa.Column("media", sa.Float(), nullable=False),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensor.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sensor_id", "data", name="uq_lectura_diaria_sensor_id_data"),
    )
    op.create_index(
        op.f("ix_lectura_diaria_sensor_id"), "lectura_diaria", ["sensor_id"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_lectura_diaria_sensor_id"), table_name="lectura_diaria")
    op.drop_table("lectura_diaria")
    op.drop_index(op.f("ix_lectura_sensor_sensor_id"), table_name="lectura_sensor")
    op.drop_index(op.f("ix_lectura_sensor_momento"), table_name="lectura_sensor")
    op.drop_table("lectura_sensor")
    op.drop_index(op.f("ix_sensor_horta_id"), table_name="sensor")
    op.drop_index(op.f("ix_sensor_clave_hash"), table_name="sensor")
    op.drop_table("sensor")
