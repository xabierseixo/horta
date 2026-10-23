"""cultivo completo e colleitas

Revision ID: f6a1c4e8b9d3
Revises: e5c9f3b7d2a4
Create Date: 2026-10-23 12:00:00

Campos do REA no cultivo, táboa colleita e paso dos datos antigos
(datas de sementeira/plantación e cantidade colleitada).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a1c4e8b9d3"
down_revision: Union[str, Sequence[str], None] = "e5c9f3b7d2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("superficie_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("tipo_inicio", sa.String(12), nullable=True))
        batch.add_column(sa.Column("data_inicio", sa.Date(), nullable=True))
        batch.add_column(sa.Column("data_fin", sa.Date(), nullable=True))
        batch.add_column(sa.Column("causa_baixa", sa.String(20), nullable=True))
        batch.add_column(sa.Column("sistema_cultivo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("sistema_explotacion", sa.String(20), nullable=True))
        batch.add_column(sa.Column("destino", sa.String(20), nullable=True))
        batch.add_column(sa.Column("actividade_agraria", sa.String(20), nullable=True))
        batch.add_column(sa.Column("certificacion_ecoloxica", sa.String(20), nullable=True))
        batch.add_column(sa.Column("data_inicio_conversion", sa.Date(), nullable=True))
        batch.add_column(
            sa.Column("producion_integrada", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("procedencia_material", sa.String(20), nullable=True))
        batch.add_column(sa.Column("provedor_material", sa.String(200), nullable=True))
        batch.add_column(sa.Column("lote_material", sa.String(40), nullable=True))
        batch.add_column(sa.Column("pasaporte_fitosanitario", sa.String(40), nullable=True))
        batch.add_column(sa.Column("ropveg", sa.String(20), nullable=True))
        batch.add_column(sa.Column("num_arbores", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("marco_plantacion", sa.String(20), nullable=True))
        batch.add_column(sa.Column("ano_plantacion", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("unidades_produtivas", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("ciclos_ano", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("duracion_ciclo_dias", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("cultivo_anterior_codigo", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("obxectivo_colleita_kg_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("tipo_mvr", sa.String(20), nullable=True))
        batch.add_column(sa.Column("detalle_mvr", sa.String(20), nullable=True))
        batch.add_column(sa.Column("empresa_semente", sa.String(20), nullable=True))
        batch.add_column(
            sa.Column("sementeira_directa", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("tipo_cobertura_solo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("num_castineiros", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_abeleiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_nogueiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_amendoeiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_outros_froitos_casca", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("data_fin_sementeira", sa.Date(), nullable=True))
        batch.add_column(sa.Column("cantidade_semente_kg", sa.Float(), nullable=True))
        batch.add_column(sa.Column("dose_sementeira_kg_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("densidade_plantas_ha", sa.Float(), nullable=True))
        batch.add_column(
            sa.Column("material_tratado", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column("material_adquirido", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("data_adquisicion_material", sa.Date(), nullable=True))
    op.create_table(
        "colleita",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cultivo_id", sa.Integer(), sa.ForeignKey("cultivo.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(20), nullable=False),
        sa.Column("superficie_ha", sa.Float(), nullable=True),
        sa.Column("lote", sa.String(40), nullable=False),
        sa.Column("albaran_factura", sa.String(60), nullable=True),
        sa.Column("destino_colleita", sa.String(20), nullable=True),
        sa.Column("destino_restos", sa.String(20), nullable=True),
        sa.Column("obten_sementes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("obten_plantas", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "sen_colleita_ambiental", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("restos_no_solo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("maquina_id", sa.Integer(), sa.ForeignKey("maquina.id"), nullable=True),
        sa.Column("num_repeticions", sa.Integer(), nullable=True),
        sa.Column("duracion_h_ha", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("uuid", sa.String(36), nullable=True, unique=True),
        sa.Column("creado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_colleita_cultivo_id", "colleita", ["cultivo_id"])
    op.execute(
        "UPDATE cultivo SET tipo_inicio = 'plantacion', data_inicio = data_plantacion "
        "WHERE data_plantacion IS NOT NULL"
    )
    op.execute(
        "UPDATE cultivo SET tipo_inicio = 'sementeira', data_inicio = data_sementeira "
        "WHERE data_inicio IS NULL AND data_sementeira IS NOT NULL"
    )
    op.execute(
        "UPDATE cultivo SET data_fin = data_colleita_real "
        "WHERE estado IN ('colleitado', 'finalizado') AND data_colleita_real IS NOT NULL"
    )
    op.execute(
        "INSERT INTO colleita (cultivo_id, data, cantidade, unidade, lote, baixa, created_at) "
        "SELECT id, COALESCE(data_colleita_real, date(created_at)), cantidade, "
        "COALESCE(unidade, 'kg'), 'MIGRADO-' || id, 0, CURRENT_TIMESTAMP "
        "FROM cultivo WHERE cantidade IS NOT NULL AND cantidade > 0"
    )


def downgrade() -> None:
    op.drop_index("ix_colleita_cultivo_id", table_name="colleita")
    op.drop_table("colleita")
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("data_adquisicion_material")
        batch.drop_column("material_adquirido")
        batch.drop_column("material_tratado")
        batch.drop_column("densidade_plantas_ha")
        batch.drop_column("dose_sementeira_kg_ha")
        batch.drop_column("cantidade_semente_kg")
        batch.drop_column("data_fin_sementeira")
        batch.drop_column("num_outros_froitos_casca")
        batch.drop_column("num_amendoeiras")
        batch.drop_column("num_nogueiras")
        batch.drop_column("num_abeleiras")
        batch.drop_column("num_castineiros")
        batch.drop_column("tipo_cobertura_solo")
        batch.drop_column("sementeira_directa")
        batch.drop_column("empresa_semente")
        batch.drop_column("detalle_mvr")
        batch.drop_column("tipo_mvr")
        batch.drop_column("obxectivo_colleita_kg_ha")
        batch.drop_column("cultivo_anterior_codigo")
        batch.drop_column("duracion_ciclo_dias")
        batch.drop_column("ciclos_ano")
        batch.drop_column("unidades_produtivas")
        batch.drop_column("ano_plantacion")
        batch.drop_column("marco_plantacion")
        batch.drop_column("num_arbores")
        batch.drop_column("ropveg")
        batch.drop_column("pasaporte_fitosanitario")
        batch.drop_column("lote_material")
        batch.drop_column("provedor_material")
        batch.drop_column("procedencia_material")
        batch.drop_column("producion_integrada")
        batch.drop_column("data_inicio_conversion")
        batch.drop_column("certificacion_ecoloxica")
        batch.drop_column("actividade_agraria")
        batch.drop_column("destino")
        batch.drop_column("sistema_explotacion")
        batch.drop_column("sistema_cultivo")
        batch.drop_column("causa_baixa")
        batch.drop_column("data_fin")
        batch.drop_column("data_inicio")
        batch.drop_column("tipo_inicio")
        batch.drop_column("superficie_ha")
