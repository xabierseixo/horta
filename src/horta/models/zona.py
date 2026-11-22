"""Zonas dunha parcela (bancais, sectores, invernadoiros…): as divisións propias da
explotación dentro dun recinto oficial. Un cultivo pode ir nunha zona."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ParcelaZona(Base):
    __tablename__ = "parcela_zona"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("parcela.id"), index=True)
    nome: Mapped[str] = mapped_column(String(80))
    # services.zonas.TIPOS_ZONA
    tipo: Mapped[str] = mapped_column(String(20), default="bancal")
    # GeoJSON Polygon, como a parcela
    geometria: Mapped[str | None] = mapped_column(Text, default=None)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)  # hectáreas
    notas: Mapped[str | None] = mapped_column(String(500), default=None)
