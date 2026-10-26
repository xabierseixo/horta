"""Rega (CUE bloque 10): cada rega dun cultivo. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Rega(Base):
    __tablename__ = "rega"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    sistema_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    boas_practicas: Mapped[list[RegaBoaPractica]] = relationship(cascade="all, delete-orphan")


class RegaBoaPractica(Base):
    __tablename__ = "rega_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
