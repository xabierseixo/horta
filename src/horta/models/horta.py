from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class RolHorta(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    LECTOR = "lector"


class Horta(Base):
    __tablename__ = "horta"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    uso_profesional: Mapped[bool] = mapped_column(Boolean, default=False)
    # O titular, o representante e o asesor son persoas con ese papel (services.persoas)
    codigo_reaga: Mapped[str | None] = mapped_column(String(14), default=None)
    codigo_rega: Mapped[str | None] = mapped_column(String(14), default=None)
    lat: Mapped[float | None] = mapped_column(Float, default=None)
    lon: Mapped[float | None] = mapped_column(Float, default=None)
    telefono: Mapped[str | None] = mapped_column(String(30), default=None)
    # Caderno de explotación (modelo da Xunta 1.1 e 1.4)
    enderezo: Mapped[str | None] = mapped_column(String(200), default=None)
    localidade: Mapped[str | None] = mapped_column(String(100), default=None)
    codigo_postal: Mapped[str | None] = mapped_column(String(10), default=None)
    provincia: Mapped[str | None] = mapped_column(String(50), default=None)
    email: Mapped[str | None] = mapped_column(String(200), default=None)
    tipo_representacion: Mapped[str | None] = mapped_column(String(100), default=None)
    tipo_xip: Mapped[str | None] = mapped_column(String(10), default=None)
    asesoramento_fertilizacion: Mapped[bool] = mapped_column(Boolean, default=False)
    foto_perfil: Mapped[str | None] = mapped_column(String(500), default=None)
    ultima_conexion: Mapped[datetime | None] = mapped_column(
        DateTime, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class HortaMembro(Base):
    __tablename__ = "horta_membro"

    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    rol: Mapped[RolHorta] = mapped_column(Enum(RolHorta), default=RolHorta.LECTOR)
