from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Animal(Base):
    __tablename__ = "animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    # Nome do grupo (p.ex. «Galiñas do galiñeiro de abaixo») e a especie no catálogo oficial
    especie: Mapped[str] = mapped_column(String(80))
    especie_codigo: Mapped[str | None] = mapped_column(String(20), default=None)
    raza: Mapped[str | None] = mapped_column(String(120), default=None)
    # Cantidade, data de baixa e estado saen dos movementos (services.movementos_animais)
    cantidade: Mapped[int] = mapped_column(Integer, default=1)
    data_alta: Mapped[date] = mapped_column(Date)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activo")
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    # Onde están (paso 14)
    # Titular dos animais se non é o da explotación (RD 787/2023, anexo V.3)
    titular_animais_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"),
                                                           default=None)
    instalacion_id: Mapped[int | None] = mapped_column(ForeignKey("instalacion.id"),
                                                      default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class AnimalIdentificado(Base):
    """Un animal identificado dentro dun grupo (opcional en todas as especies; obrigatorio no
    vacún, ovino, caprino e équidos: Reg. UE 2016/429 e Reg. Delegado 2019/2035)."""

    __tablename__ = "animal_identificado"

    id: Mapped[int] = mapped_column(primary_key=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    # Crotal, microchip, anela…
    identificador: Mapped[str] = mapped_column(String(50))
    nome: Mapped[str | None] = mapped_column(String(80), default=None)
    sexo: Mapped[str | None] = mapped_column(String(10), default=None)
    # Tipo de dispositivo de identificación (RD 787/2023, anexo V.8)
    dispositivo: Mapped[str | None] = mapped_column(String(20), default=None)
    data_nacemento: Mapped[date | None] = mapped_column(Date, default=None)
    data_alta: Mapped[date] = mapped_column(Date)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    notas: Mapped[str | None] = mapped_column(String(500), default=None)
