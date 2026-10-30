"""Tratamentos non ligados á superficie (caderno 3.3–3.5; CUE 1.2–1.3): postcolleita,
locais de almacenamento e medios de transporte. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun

TIPOS_INSTALACION = {"postcolleita": "Postcolleita (no produto vexetal)",
                     "local": "Local de almacenamento", "transporte": "Medio de transporte"}


class TratamentoInstalacion(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "tratamento_instalacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    data: Mapped[date] = mapped_column(Date)
    # Que se trata: produto vexetal; local (tipo e enderezo); vehículo (tipo, modelo, matrícula)
    obxecto: Mapped[str] = mapped_column(String(250))
    referencia_catastral: Mapped[str | None] = mapped_column(String(30), default=None)
    problema_tipo: Mapped[str | None] = mapped_column(String(20), default=None)
    problema_codigo: Mapped[str | None] = mapped_column(String(20), default=None)
    xustificacion: Mapped[str | None] = mapped_column(String(20), default=None)
    # t de produto vexetal (postcolleita) ou m³ (locais e transporte)
    cantidade_tratada: Mapped[float | None] = mapped_column(Float, default=None)
    tipo_produto: Mapped[str | None] = mapped_column(String(20), default=None)
    nome_comercial: Mapped[str | None] = mapped_column(String(250), default=None)
    num_rexistro: Mapped[str | None] = mapped_column(String(50), default=None)
    materia_activa: Mapped[str | None] = mapped_column(String(250), default=None)
    cantidade_utilizada: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    # CUE 1.2–1.3: produto vexetal tratado (lista oficial de cultivos), instalación
    # (local de almacenamento) e eficacia do tratamento
    produto_vexetal: Mapped[int | None] = mapped_column(Integer, default=None)
    instalacion_id: Mapped[int | None] = mapped_column(ForeignKey("instalacion.id"),
                                                         default=None)
    eficacia: Mapped[str | None] = mapped_column(String(20), default=None)
