"""Recomendacións do asesor fitosanitario (mellora N7)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base

ESTADOS_RECOMENDACION = ("pendente", "aplicada", "descartada")


class Recomendacion(Base):
    __tablename__ = "recomendacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    asesor_persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    data: Mapped[date] = mapped_column(Date)
    valida_ata: Mapped[date | None] = mapped_column(Date, default=None)
    cultivos: Mapped[list[dict]] = mapped_column(JSON, default=list)
    problemas: Mapped[list[dict]] = mapped_column(JSON, default=list)
    xustificacions: Mapped[list[str]] = mapped_column(JSON, default=list)
    produtos: Mapped[list[dict]] = mapped_column(JSON, default=list)
    medidas: Mapped[list[dict]] = mapped_column(JSON, default=list)
    observacions: Mapped[str | None] = mapped_column(Text, default=None)
    estado: Mapped[str] = mapped_column(String(12), default="pendente")
    motivo_descarte: Mapped[str | None] = mapped_column(String(300), default=None)
    tratamento_id: Mapped[int | None] = mapped_column(
        ForeignKey("tratamento_fito.id"), default=None
    )
    visita_id: Mapped[int | None] = mapped_column(
        ForeignKey("visita_campo.id"), default=None
    )
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
