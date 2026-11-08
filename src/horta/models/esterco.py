"""Movementos de estercos e puríns: cesións e recepcións (RD 1051/2022). Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.persoa import Persoa
from horta.models.traballo import FeitoPor, ParteComun


class MovementoEsterco(ParteComun, FeitoPor, Base):
    """Cesión ou recepción de esterco ou purín con outra explotación ou xestor."""

    __tablename__ = "movemento_esterco"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # "cesion" (sae da nosa explotación) ou "recepcion" (entra)
    tipo: Mapped[str] = mapped_column(String(10))
    data: Mapped[date] = mapped_column(Date)
    # A outra parte interveniente (Contactos)
    outra_parte_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"), index=True)
    outra_parte_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_explotacion: Mapped[str] = mapped_column(String(100))
    # Especie animal segundo o catálogo de especies (services.animais.ESPECIES)
    tipo_animais: Mapped[str] = mapped_column(String(30))
    # Código do catálogo material_fertilizante (só estercos e puríns)
    material: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(10))
    # Composición agronómica en % sobre materia fresca (anexo VII RD 1051/2022)
    n_total: Mapped[float | None] = mapped_column(Float, default=None)
    p2o5: Mapped[float | None] = mapped_column(Float, default=None)
    k2o: Mapped[float | None] = mapped_column(Float, default=None)
    materia_organica: Mapped[float | None] = mapped_column(Float, default=None)
    # "analise", "programa" ou "condutivimetro"
    orixe_composicion: Mapped[str | None] = mapped_column(String(20), default=None)
    parcelas_destino: Mapped[str | None] = mapped_column(String(300), default=None)

    outra_parte: Mapped[Persoa] = relationship(foreign_keys=[outra_parte_id])
