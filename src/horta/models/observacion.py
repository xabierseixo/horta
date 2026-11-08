"""Observacións e limiares de pragas, enfermidades e malas herbas (GIP)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class ObservacionPraga(ParteComun, FeitoPor, Base):
    """Observación de pragas, enfermidades ou malas herbas nun cultivo (GIP)."""

    __tablename__ = "observacion_praga"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    problema_tipo: Mapped[str] = mapped_column(String(20))
    problema_codigo: Mapped[str] = mapped_column(String(20))
    metodo: Mapped[str] = mapped_column(String(20))
    conto: Mapped[float | None] = mapped_column(Float, default=None)
    unidade_conto: Mapped[str | None] = mapped_column(String(30), default=None)
    nivel: Mapped[str | None] = mapped_column(String(10), default=None)
    estado_fenoloxico: Mapped[str | None] = mapped_column(String(20), default=None)


class LimiarPraga(Base):
    """Limiar de intervención para unha praga ou enfermidade (GIP)."""

    __tablename__ = "limiar_praga"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    problema_tipo: Mapped[str] = mapped_column(String(20))
    problema_codigo: Mapped[str] = mapped_column(String(20))
    metodo: Mapped[str] = mapped_column(String(20))
    unidade_conto: Mapped[str] = mapped_column(String(30))
    valor: Mapped[float] = mapped_column(Float)
    fonte: Mapped[str] = mapped_column(String(300))
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
