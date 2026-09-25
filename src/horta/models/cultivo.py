from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Cultivo(Base):
    __tablename__ = "cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("parcela.id"))
    especie: Mapped[str] = mapped_column(String(120))
    variedade: Mapped[str | None] = mapped_column(String(120), default=None)
    data_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    data_plantacion: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_real: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(30), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Tratamento(Base):
    __tablename__ = "tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    praga: Mapped[str] = mapped_column(String(200))
    superficie_tratada: Mapped[float | None] = mapped_column(Float, default=None)
    produto: Mapped[str] = mapped_column(String(200))
    numero_rexistro_produto: Mapped[str | None] = mapped_column(String(50), default=None)
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(200), default=None)
    aplicador: Mapped[str] = mapped_column(String(200))
    equipo_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    persoas_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Fertilizacion(Base):
    __tablename__ = "fertilizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
    tipo: Mapped[str] = mapped_column(String(50))
    produto: Mapped[str] = mapped_column(String(200))
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    n: Mapped[float | None] = mapped_column(Float, default=None)
    p: Mapped[float | None] = mapped_column(Float, default=None)
    k: Mapped[float | None] = mapped_column(Float, default=None)
    carbono_organico: Mapped[float | None] = mapped_column(Float, default=None)
    micronutrientes: Mapped[str | None] = mapped_column(String(300), default=None)
    asesoramento_recibido: Mapped[str | None] = mapped_column(String(300), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
