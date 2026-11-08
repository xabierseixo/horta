"""Dispositivo móbil con clave propia para a app do campo (PWA sen cobertura)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Dispositivo(Base):
    """Dispositivo móbil con clave propia para acceder á API do campo."""

    __tablename__ = "dispositivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), index=True)
    nome: Mapped[str] = mapped_column(String(100))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    ultimo_uso: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    revogado: Mapped[bool] = mapped_column(Boolean, default=False)
