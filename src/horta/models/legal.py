"""Configuración legal e responsable do tratamento dos datos (RGPD)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ConfiguracionLegal(Base):
    """Datos do responsable do tratamento (LSSI e RGPD). Unha soa fila na aplicación."""

    __tablename__ = "configuracion_legal"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(50), default=None)
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    correo: Mapped[str | None] = mapped_column(String(255), default=None)
    dpd: Mapped[str | None] = mapped_column(String(255), default=None)
    localizacion: Mapped[str | None] = mapped_column(Text, default=None)
    actualizado_en: Mapped[datetime | None] = mapped_column(DateTime, default=None)
