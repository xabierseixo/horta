"""Tratamento fitosanitario conforme ao bloque TratamFito do descritor CUE (FEGA v3.11.4)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base

TIPOS_PROBLEMA = ("enfermidade", "praga", "mala_herba", "regulador")


class TratamentoFito(Base):
    __tablename__ = "tratamento_fito"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    hora: Mapped[time | None] = mapped_column(Time, default=None)
    actividade_cuberta: Mapped[str | None] = mapped_column(String(20), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(20), default=None)
    observacions: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    orixinal_produto: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_dose: Mapped[str | None] = mapped_column(String(100), default=None)
    orixinal_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_equipo: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    tratamento_antigo_id: Mapped[int | None] = mapped_column(Integer, default=None)

    cultivos: Mapped[list[TratamentoCultivo]] = relationship(cascade="all, delete-orphan")
    problemas: Mapped[list[TratamentoProblema]] = relationship(cascade="all, delete-orphan")
    xustificacions: Mapped[list[TratamentoXustificacion]] = relationship(
        cascade="all, delete-orphan"
    )
    produtos: Mapped[list[TratamentoProduto]] = relationship(cascade="all, delete-orphan")
    medidas: Mapped[list[TratamentoMedida]] = relationship(cascade="all, delete-orphan")
    aplicadores: Mapped[list[TratamentoAplicador]] = relationship(cascade="all, delete-orphan")
    asesor: Mapped[TratamentoAsesor | None] = relationship(
        cascade="all, delete-orphan", uselist=False
    )


class TratamentoCultivo(Base):
    __tablename__ = "tratamento_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    estado_fenoloxico: Mapped[str | None] = mapped_column(String(20), default=None)


class TratamentoProblema(Base):
    __tablename__ = "tratamento_problema"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    codigo: Mapped[str] = mapped_column(String(20))


class TratamentoXustificacion(Base):
    __tablename__ = "tratamento_xustificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class TratamentoProduto(Base):
    __tablename__ = "tratamento_produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo_produto: Mapped[str] = mapped_column(String(20))
    num_rexistro: Mapped[str | None] = mapped_column(String(20), default=None)
    nome_comercial: Mapped[str | None] = mapped_column(String(200), default=None)
    materia_activa: Mapped[str | None] = mapped_column(String(200), default=None)
    dose: Mapped[float | None] = mapped_column(Float, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))


class TratamentoMedida(Base):
    __tablename__ = "tratamento_medida"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo_medida: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    num_rexistro_mdf: Mapped[str | None] = mapped_column(String(10), default=None)
    boas_practicas: Mapped[str | None] = mapped_column(String(20), default=None)


class TratamentoAplicador(Base):
    __tablename__ = "tratamento_aplicador"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    aplicacion_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    horas_utilizacion: Mapped[float | None] = mapped_column(Float, default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion: Mapped[float | None] = mapped_column(Float, default=None)


class TratamentoAsesor(Base):
    __tablename__ = "tratamento_asesor"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), unique=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    data: Mapped[date | None] = mapped_column(Date, default=None)
    validacion: Mapped[bool] = mapped_column(Boolean, default=False)
    observacions: Mapped[str | None] = mapped_column(String(200), default=None)
    confirmacion: Mapped[bool] = mapped_column(Boolean, default=False)
    contrato: Mapped[bool] = mapped_column(Boolean, default=False)
