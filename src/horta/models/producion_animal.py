"""Produción de cada grupo de animais (ovos, leite, mel...), co seu lote, como as colleitas dos
cultivos (README §7). Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class ProducionAnimal(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "producion_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # Un período (p.ex. os ovos da semana); igual á data se é un só día
    data_fin: Mapped[date] = mapped_column(Date)
    # services.producions_animais.PRODUTOS
    produto: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    # O que non vale: rotos, ou o que se tira polo tempo de espera dun medicamento
    retirada: Mapped[float | None] = mapped_column(Float, default=None)
    # Trazabilidade (Reg. CE 178/2002 art. 18): único na explotación, xunto cos das colleitas
    lote: Mapped[str] = mapped_column(String(40))
