from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Animal(Base):
    __tablename__ = "animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    especie: Mapped[str] = mapped_column(String(80))
    raza: Mapped[str | None] = mapped_column(String(120), default=None)
    cantidade: Mapped[int] = mapped_column(Integer, default=1)
    data_alta: Mapped[date] = mapped_column(Date)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activo")
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
