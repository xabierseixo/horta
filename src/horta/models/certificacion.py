"""Modelos de certificacións e autoavaliación de calidade (tarefa 182c)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Certificacion(Base):
    __tablename__ = "certificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    esquema: Mapped[str] = mapped_column(String(30))
    nome: Mapped[str | None] = mapped_column(String(120), default=None)
    numero: Mapped[str | None] = mapped_column(String(40), default=None)
    entidade: Mapped[str | None] = mapped_column(String(120), default=None)
    data_inicio: Mapped[date | None] = mapped_column(Date, default=None)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    documento_id: Mapped[int | None] = mapped_column(ForeignKey("documento.id"), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    puntos: Mapped[list[PuntoAutoavaliacion]] = relationship(
        "PuntoAutoavaliacion", back_populates="certificacion", cascade="all, delete-orphan"
    )


class PuntoAutoavaliacion(Base):
    __tablename__ = "punto_autoavaliacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    certificacion_id: Mapped[int] = mapped_column(ForeignKey("certificacion.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    punto: Mapped[str] = mapped_column(String(30))
    resultado: Mapped[str] = mapped_column(String(12))
    evidencia: Mapped[str | None] = mapped_column(String(500), default=None)
    documento_id: Mapped[int | None] = mapped_column(ForeignKey("documento.id"), default=None)
    accion_correctora: Mapped[str | None] = mapped_column(String(500), default=None)
    data_correccion: Mapped[date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    certificacion: Mapped[Certificacion] = relationship(
        "Certificacion", back_populates="puntos"
    )
