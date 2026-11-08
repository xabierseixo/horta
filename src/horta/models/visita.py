"""Visitas de campo do persoal asesor técnico (mellora N7)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Text, Time
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class VisitaCampo(Base):
    """Visita de campo da persoa asesora técnica ou persoal técnico (GIP)."""

    __tablename__ = "visita_campo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    asesor_persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    data: Mapped[date] = mapped_column(Date)
    hora_inicio: Mapped[time | None] = mapped_column(Time, default=None)
    cultivos: Mapped[list[int]] = mapped_column(JSON, default=list)
    estado_xeral: Mapped[str | None] = mapped_column(Text, default=None)
    conclusions: Mapped[str | None] = mapped_column(Text, default=None)
    proxima_visita: Mapped[date | None] = mapped_column(Date, default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
