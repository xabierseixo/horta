"""Produción de cada grupo de animais (ovos, leite, mel...), co seu lote, como as colleitas dos
cultivos (README §7). Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ProducionAnimal(Base):
    __tablename__ = "producion_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # Un período (p.ex. os ovos da semana); igual á data se é un só día
    data_fin: Mapped[date] = mapped_column(Date)
    # services.producions_animais.PRODUTOS
    produto: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    # O que non vale: rotos, ou o que se tira polo tempo de espera dun medicamento
    retirada: Mapped[float | None] = mapped_column(Float, default=None)
    # Trazabilidade (Reg. CE 178/2002 art. 18): único na explotación, xunto cos das colleitas
    lote: Mapped[str] = mapped_column(String(40))
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
