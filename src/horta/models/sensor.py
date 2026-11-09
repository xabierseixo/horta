"""Modelos para sensores IoT e lecturas (tarefa 183a)."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Sensor(Base):
    """Sensor da explotación (humidade, temperatura, choiva, contador, nivel…)."""

    __tablename__ = "sensor"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(100))
    tipo: Mapped[str] = mapped_column(String(30))
    unidade: Mapped[str] = mapped_column(String(20))
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    instalacion_id: Mapped[int | None] = mapped_column(ForeignKey("instalacion.id"), default=None)
    clave_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    campo_payload: Mapped[str | None] = mapped_column(String(60), default=None)
    limiar_min: Mapped[float | None] = mapped_column(Float, default=None)
    limiar_max: Mapped[float | None] = mapped_column(Float, default=None)
    ultima_lectura_en: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    compactado_ata: Mapped[date | None] = mapped_column(Date, default=None)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class LecturaSensor(Base):
    """Lectura individual dun sensor con momento e valor."""

    __tablename__ = "lectura_sensor"
    __table_args__ = (UniqueConstraint("sensor_id", "momento"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("sensor.id"), index=True)
    momento: Mapped[datetime] = mapped_column(DateTime, index=True)
    valor: Mapped[float] = mapped_column(Float)


class LecturaDiaria(Base):
    """Resumo diario compactado das lecturas dun sensor."""

    __tablename__ = "lectura_diaria"
    __table_args__ = (UniqueConstraint("sensor_id", "data"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    sensor_id: Mapped[int] = mapped_column(ForeignKey("sensor.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    minimo: Mapped[float] = mapped_column(Float)
    maximo: Mapped[float] = mapped_column(Float)
    media: Mapped[float] = mapped_column(Float)
    n: Mapped[int] = mapped_column(Integer)
