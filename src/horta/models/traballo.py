"""Parte común de todos os traballos (a documentación): escríbese unha vez aquí
para que ningún traballo quede sen ela. Cada traballo herda as partes que lle tocan."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class ParteComun:
    """Notas, baixa lóxica, identificador do móbil e quen o apuntou: en todos os traballos."""

    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    # Trazabilidade: quen apuntou o traballo
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class FeitoPor:
    """Quen o fixo e cantas horas (no tratamento, cada aplicador)."""

    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)


class ConMaquina:
    """Con que máquina, nos traballos onde pode haber unha."""

    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
