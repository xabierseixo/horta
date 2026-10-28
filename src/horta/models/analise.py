"""Análises (CUE bloque 13, se se fixeron): de cultivo, produto colleitado, solo ou auga."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Analise(ParteComun, FeitoPor, Base):
    __tablename__ = "analise"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    material_analizado: Mapped[str] = mapped_column(String(20))
    data_mostraxe: Mapped[date] = mapped_column(Date)
    laboratorio_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    num_boletin: Mapped[str | None] = mapped_column(String(50), default=None)
    # Onde: opcionais. colleita_id liga a análise do produto co seu lote (trazabilidade).
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
    # Parámetros do solo (CUE ParametrosSuelo): só se o material é solo
    materia_organica: Mapped[float | None] = mapped_column(Float, default=None)
    area: Mapped[float | None] = mapped_column(Float, default=None)
    limo: Mapped[float | None] = mapped_column(Float, default=None)
    arxila: Mapped[float | None] = mapped_column(Float, default=None)
    ph: Mapped[float | None] = mapped_column(Float, default=None)
    fosforo_ppm: Mapped[float | None] = mapped_column(Float, default=None)
    potasio_ppm: Mapped[float | None] = mapped_column(Float, default=None)
    n_total: Mapped[float | None] = mapped_column(Float, default=None)
    conductividade: Mapped[float | None] = mapped_column(Float, default=None)
    # Metais pesados no solo (mg/kg s.m.s.), caderno 6: obrigatorios se se aplican lodos
    cadmio: Mapped[float | None] = mapped_column(Float, default=None)
    cobre: Mapped[float | None] = mapped_column(Float, default=None)
    niquel: Mapped[float | None] = mapped_column(Float, default=None)
    chumbo: Mapped[float | None] = mapped_column(Float, default=None)
    zinc: Mapped[float | None] = mapped_column(Float, default=None)
    mercurio: Mapped[float | None] = mapped_column(Float, default=None)
    cromo: Mapped[float | None] = mapped_column(Float, default=None)

    tipos: Mapped[list[AnaliseTipo]] = relationship(cascade="all, delete-orphan")
    substancias: Mapped[list[AnaliseSubstancia]] = relationship(cascade="all, delete-orphan")


class AnaliseTipo(Base):
    __tablename__ = "analise_tipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class AnaliseSubstancia(Base):
    __tablename__ = "analise_substancia"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
