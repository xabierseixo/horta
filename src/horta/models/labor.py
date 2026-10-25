"""Labor cultural (CUE bloque 5): cada labor feito nun cultivo. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Labor(Base):
    __tablename__ = "labor"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float] = mapped_column(Float)
    tipo_labor: Mapped[str] = mapped_column(String(20))
    restos_desbroce_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_poda_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
