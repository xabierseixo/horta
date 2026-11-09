from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class EstimacionColleita(Base):
    """Estimación da colleita antes da recollida (por mostraxe ou directa)."""

    __tablename__ = "estimacion_colleita"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    metodo: Mapped[str] = mapped_column(String(20))
    plantas_ha: Mapped[float | None] = mapped_column(Float, default=None)
    unidades_planta: Mapped[float | None] = mapped_column(Float, default=None)
    peso_unidade_g: Mapped[float | None] = mapped_column(Float, default=None)
    kg_ha: Mapped[float] = mapped_column(Float)
    notas: Mapped[str | None] = mapped_column(String(500), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
