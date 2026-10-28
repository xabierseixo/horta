"""Labor cultural (CUE bloque 5): cada labor, nunha ou varias leiras. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Labor(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "labor"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    tipo_labor: Mapped[str] = mapped_column(String(20))
    restos_desbroce_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_poda_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
    # As leiras (cultivos) onde se fixo: unha ou varias
    #
    leiras: Mapped[list[LaborCultivo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class LaborCultivo(Base):
    """Cada leira (cultivo) dun labor, coa superficie onde se fixo."""

    __tablename__ = "labor_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    labor_id: Mapped[int] = mapped_column(ForeignKey("labor.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
