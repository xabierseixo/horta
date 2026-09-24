from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
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
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class HortaMembro(Base):
    __tablename__ = "horta_membro"

    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("usuario.id"), primary_key=True)
    rol: Mapped[RolHorta] = mapped_column(Enum(RolHorta), default=RolHorta.LECTOR)
