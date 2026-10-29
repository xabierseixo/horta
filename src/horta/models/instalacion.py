"""Instalacións da explotación (paso 14): almacéns, galiñeiros, cortes, invernadoiros…
Os animais e outros traballos poden ir a unha instalación."""

from __future__ import annotations

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Instalacion(Base):
    __tablename__ = "instalacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # services.instalacions.TIPOS_INSTALACION
    tipo: Mapped[str] = mapped_column(String(20))
    nome: Mapped[str] = mapped_column(String(120))
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    referencia_catastral: Mapped[str | None] = mapped_column(String(30), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
