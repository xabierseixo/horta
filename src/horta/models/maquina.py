from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Maquina(Base):
    __tablename__ = "maquina"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    alias: Mapped[str] = mapped_column(String(120))
    tipo_une: Mapped[str | None] = mapped_column(String(20), default=None)
    marca_modelo: Mapped[str | None] = mapped_column(String(200), default=None)
    num_roma: Mapped[str | None] = mapped_column(String(12), default=None)
    num_reganip: Mapped[str | None] = mapped_column(String(12), default=None)
    id_equipo_non_inscribible: Mapped[str | None] = mapped_column(String(50), default=None)
    propia: Mapped[bool] = mapped_column(Boolean, default=True)
    potencia: Mapped[float | None] = mapped_column(Float, default=None)
    unidade_potencia: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    data_ultima_inspeccion: Mapped[date | None] = mapped_column(Date, default=None)
    data_adquisicion: Mapped[date | None] = mapped_column(Date, default=None)
    alugada: Mapped[bool] = mapped_column(Boolean, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
