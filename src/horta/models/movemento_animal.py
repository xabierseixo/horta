"""Entradas e saídas de animais de cada grupo (libro de rexistro gandeiro, RD 787/2023 anexo
V 9 e 10). A cantidade do grupo é a suma dos seus movementos. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class MovementoAnimal(Base):
    __tablename__ = "movemento_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # services.movementos_animais.TIPOS_MOVEMENTO
    tipo: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[int] = mapped_column(Integer)
    identificacion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Entrada: o titular anterior e a explotación de orixe; saída: o novo e a de destino
    titular: Mapped[str | None] = mapped_column(String(300), default=None)
    rega: Mapped[str | None] = mapped_column(String(20), default=None)
    codigo_movemento: Mapped[str | None] = mapped_column(String(50), default=None)
    # Morte ou sacrificio
    causa: Mapped[str | None] = mapped_column(String(300), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
