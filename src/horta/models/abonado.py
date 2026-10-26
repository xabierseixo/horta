"""Fertilización (CUE bloque 9): os abonos de cada explotación e cada abonado. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Fertilizante(Base):
    """Un abono da explotación ("Os meus abonos"): gárdase unha vez e escóllese ao abonar."""

    __tablename__ = "fertilizante"
    __table_args__ = (UniqueConstraint("horta_id", "nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(250))
    material: Mapped[str] = mapped_column(String(20))
    fertilizante_siex_codigo: Mapped[int | None] = mapped_column(
        ForeignKey("fertilizante_siex.codigo"), default=None
    )
    n_pct: Mapped[float | None] = mapped_column(Float, default=None)
    p2o5_pct: Mapped[float | None] = mapped_column(Float, default=None)
    k2o_pct: Mapped[float | None] = mapped_column(Float, default=None)
    # Valor agronómico (caderno 7): formas do N, P soluble e materia orgánica (estercos)
    n_organico_pct: Mapped[float | None] = mapped_column(Float, default=None)
    n_ureico_pct: Mapped[float | None] = mapped_column(Float, default=None)
    n_nitrico_pct: Mapped[float | None] = mapped_column(Float, default=None)
    n_amoniacal_pct: Mapped[float | None] = mapped_column(Float, default=None)
    p2o5_soluble_pct: Mapped[float | None] = mapped_column(Float, default=None)
    materia_organica_pct: Mapped[float | None] = mapped_column(Float, default=None)
    # Metais pesados en mg/kg s.m.s. (só residuos valorizables, anexo VIII RD 1051/2022)
    cadmio: Mapped[float | None] = mapped_column(Float, default=None)
    cobre: Mapped[float | None] = mapped_column(Float, default=None)
    niquel: Mapped[float | None] = mapped_column(Float, default=None)
    chumbo: Mapped[float | None] = mapped_column(Float, default=None)
    zinc: Mapped[float | None] = mapped_column(Float, default=None)
    mercurio: Mapped[float | None] = mapped_column(Float, default=None)
    cromo_vi: Mapped[float | None] = mapped_column(Float, default=None)
    arsenico: Mapped[float | None] = mapped_column(Float, default=None)
    cromo: Mapped[float | None] = mapped_column(Float, default=None)
    liquido: Mapped[bool] = mapped_column(Boolean, default=False)
    densidade: Mapped[float | None] = mapped_column(Float, default=None)  # kg/L
    tratamento_estercos: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_nome: Mapped[str | None] = mapped_column(String(150), default=None)
    provedor_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_rega: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_nima: Mapped[str | None] = mapped_column(String(50), default=None)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Abonado(Base):
    """Cada aplicación de abono a un cultivo."""

    __tablename__ = "abonado"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    fertilizante_id: Mapped[int | None] = mapped_column(ForeignKey("fertilizante.id"), default=None)
    dose: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_fertilizacion: Mapped[str | None] = mapped_column(String(20), default=None)
    metodo: Mapped[str | None] = mapped_column(String(20), default=None)
    xestion_sostible: Mapped[bool] = mapped_column(Boolean, default=False)
    aplicacion_lodos: Mapped[bool] = mapped_column(Boolean, default=False)
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
    aplicador_persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    empresa_servizos_regfer: Mapped[str | None] = mapped_column(String(50), default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    boas_practicas: Mapped[list[AbonadoBoaPractica]] = relationship(
        cascade="all, delete-orphan"
    )


class AbonadoBoaPractica(Base):
    __tablename__ = "abonado_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    abonado_id: Mapped[int] = mapped_column(ForeignKey("abonado.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
