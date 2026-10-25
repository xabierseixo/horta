"""Última comprobación de cada fonte que se actualiza soa (aínda que non houbese cambios)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ComprobacionCatalogo(Base):
    __tablename__ = "comprobacion_catalogo"

    catalogo: Mapped[str] = mapped_column(String(60), primary_key=True)
    data: Mapped[datetime] = mapped_column(DateTime)
    erro: Mapped[str | None] = mapped_column(String(500), default=None)
