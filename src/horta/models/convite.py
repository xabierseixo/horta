"""Convite para entrar nunha explotación (o deseño
§2bis): quen administra a explotación xera unha ligazón para unha persoa do equipo; ao abrila,
esa persoa entra coa súa conta ou crea unha co seu propio contrasinal."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.horta import RolHorta


class Convite(Base):
    __tablename__ = "convite"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(String(64), unique=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    rol: Mapped[RolHorta] = mapped_column(Enum(RolHorta))
    creado_por: Mapped[int] = mapped_column(ForeignKey("usuario.id"))
    caduca: Mapped[datetime] = mapped_column(DateTime)
    usado: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    acceso_ata: Mapped[date | None] = mapped_column(Date, default=None)
    motivo: Mapped[str | None] = mapped_column(String(30), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
