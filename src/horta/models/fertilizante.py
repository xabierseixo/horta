"""Abonos: catálogo oficial de produtos fertilizantes do FEGA (DETALLE_MATERIAL_FERT)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class FertilizanteSiex(Base):
    """Produto fertilizante oficial: material SIEX, nome comercial, fabricante e riqueza."""

    __tablename__ = "fertilizante_siex"

    codigo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    material: Mapped[str] = mapped_column(String(20), index=True)
    clase: Mapped[str | None] = mapped_column(String(60), default=None)
    subclase: Mapped[str | None] = mapped_column(String(60), default=None)
    nome: Mapped[str] = mapped_column(String(300))
    fabricante: Mapped[str | None] = mapped_column(String(200), default=None)
    n_pct: Mapped[float] = mapped_column(Float, default=0)
    p2o5_pct: Mapped[float] = mapped_column(Float, default=0)
    k2o_pct: Mapped[float] = mapped_column(Float, default=0)
    liquido: Mapped[bool] = mapped_column(Boolean, default=False)
    densidade: Mapped[float | None] = mapped_column(Float, default=None)
    inhibidor_nitrificacion: Mapped[bool] = mapped_column(Boolean, default=False)
    inhibidor_ureasa: Mapped[bool] = mapped_column(Boolean, default=False)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))
