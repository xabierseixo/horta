from __future__ import annotations

import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class SecanoRegadio(enum.Enum):
    SECANO = "secano"
    REGADIO = "regadio"


class Parcela(Base):
    __tablename__ = "parcela"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    nome: Mapped[str] = mapped_column(String(120))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
    posicion: Mapped[str | None] = mapped_column(String(120), default=None)
    uso_aproveitamento: Mapped[str | None] = mapped_column(String(120), default=None)
    secano_regadio: Mapped[SecanoRegadio | None] = mapped_column(
        Enum(SecanoRegadio), default=None
    )
    sigpac_provincia: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_concello: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_poligono: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_parcela: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_subparcela: Mapped[str | None] = mapped_column(String(10), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="activa")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
