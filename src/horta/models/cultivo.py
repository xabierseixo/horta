from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Cultivo(Base):
    __tablename__ = "cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("parcela.id"))
    especie: Mapped[str] = mapped_column(String(120))
    variedade: Mapped[str | None] = mapped_column(String(120), default=None)
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(
        ForeignKey("cultivo_siex.codigo"), default=None
    )
    variedade_siex_id: Mapped[int | None] = mapped_column(
        ForeignKey("variedade_siex.id"), default=None
    )
    variedade_local_id: Mapped[int | None] = mapped_column(
        ForeignKey("variedade_local.id"), default=None
    )
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
    # Campos do REA (deseño 2026-10-23-cultivo-e-colleitas). Superficie en hectáreas.
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    tipo_inicio: Mapped[str | None] = mapped_column(String(12), default=None)
    data_inicio: Mapped[date | None] = mapped_column(Date, default=None)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    causa_baixa: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_cultivo: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_explotacion: Mapped[str | None] = mapped_column(String(20), default=None)
    destino: Mapped[str | None] = mapped_column(String(20), default=None)
    actividade_agraria: Mapped[str | None] = mapped_column(String(20), default=None)
    certificacion_ecoloxica: Mapped[str | None] = mapped_column(String(20), default=None)
    data_inicio_conversion: Mapped[date | None] = mapped_column(Date, default=None)
    producion_integrada: Mapped[bool] = mapped_column(Boolean, default=False)
    procedencia_material: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_material: Mapped[str | None] = mapped_column(String(200), default=None)
    lote_material: Mapped[str | None] = mapped_column(String(40), default=None)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
    ropveg: Mapped[str | None] = mapped_column(String(20), default=None)
    num_arbores: Mapped[int | None] = mapped_column(Integer, default=None)
    marco_plantacion: Mapped[str | None] = mapped_column(String(20), default=None)
    ano_plantacion: Mapped[int | None] = mapped_column(Integer, default=None)
    unidades_produtivas: Mapped[int | None] = mapped_column(Integer, default=None)
    ciclos_ano: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_ciclo_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    cultivo_anterior_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    obxectivo_colleita_kg_ha: Mapped[float | None] = mapped_column(Float, default=None)
    # Plan de abonado (CUE 9, campos 41-49): necesidades en UF/ha e auga de rega
    plan_necesidade_n: Mapped[float | None] = mapped_column(Float, default=None)
    plan_necesidade_p2o5: Mapped[float | None] = mapped_column(Float, default=None)
    plan_necesidade_k2o: Mapped[float | None] = mapped_column(Float, default=None)
    plan_ferramenta_sostibilidade: Mapped[bool] = mapped_column(Boolean, default=False)
    plan_data: Mapped[date | None] = mapped_column(Date, default=None)
    plan_auga_n_nitrico: Mapped[float | None] = mapped_column(Float, default=None)
    plan_auga_p2o5: Mapped[float | None] = mapped_column(Float, default=None)
    # REA 12 (material vexetal, cobertura, froitos de casca) e CUE 6 (sementeira/plantación)
    tipo_mvr: Mapped[str | None] = mapped_column(String(20), default=None)
    detalle_mvr: Mapped[str | None] = mapped_column(String(20), default=None)
    empresa_semente: Mapped[str | None] = mapped_column(String(20), default=None)
    sementeira_directa: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura_solo: Mapped[str | None] = mapped_column(String(20), default=None)
    num_castineiros: Mapped[int | None] = mapped_column(Integer, default=None)
    num_abeleiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_nogueiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_amendoeiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_outros_froitos_casca: Mapped[int | None] = mapped_column(Integer, default=None)
    data_fin_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade_semente_kg: Mapped[float | None] = mapped_column(Float, default=None)
    dose_sementeira_kg_ha: Mapped[float | None] = mapped_column(Float, default=None)
    densidade_plantas_ha: Mapped[float | None] = mapped_column(Float, default=None)
    material_tratado: Mapped[bool] = mapped_column(Boolean, default=False)
    # Caderno 3.2 (semente tratada): produto co que vén tratada
    semente_tratamento_produto: Mapped[str | None] = mapped_column(String(250), default=None)
    semente_tratamento_num_rexistro: Mapped[str | None] = mapped_column(String(50), default=None)
    material_adquirido: Mapped[bool] = mapped_column(Boolean, default=False)
    data_adquisicion_material: Mapped[date | None] = mapped_column(Date, default=None)
    # Quen fixo a sementeira ou plantación e cantas horas
    sementeira_persoa_id: Mapped[int | None] = mapped_column(
        ForeignKey("persoa.id"), default=None
    )
    sementeira_horas: Mapped[float | None] = mapped_column(Float, default=None)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
