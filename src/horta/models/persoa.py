from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class TipoCarne(enum.Enum):
    basico = "basico"
    cualificado = "cualificado"
    fumigador = "fumigador"
    piloto = "piloto"
    sector_suministrador = "sector_suministrador"
    sector_tratamentos = "sector_tratamentos"


class Persoa(Base):
    __tablename__ = "persoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    apelidos: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(9), default=None)
    e_aplicador: Mapped[bool] = mapped_column(Boolean, default=False)
    e_asesor: Mapped[bool] = mapped_column(Boolean, default=False)
    ropo_numero: Mapped[str | None] = mapped_column(String(14), default=None)
    ropo_tipo_carne: Mapped[TipoCarne | None] = mapped_column(Enum(TipoCarne), default=None)
    ropo_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    regfer_numero: Mapped[str | None] = mapped_column(String(20), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
