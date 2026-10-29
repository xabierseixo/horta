"""Outro traballo (mantemento, limpeza, arranxos…): o que non é de ningún libro oficial pero
tamén leva horas. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class OutroTraballo(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "outro_traballo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    descricion: Mapped[str] = mapped_column(String(300))
    # A que se refire: unha parcela, uns animais ou (sen ningún) a explotación enteira
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    animal_id: Mapped[int | None] = mapped_column(ForeignKey("animal.id"), default=None)
