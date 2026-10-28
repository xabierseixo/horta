"""Pastoreo (CUE bloque 12): o gando nunha ou máis leiras entre dúas datas. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Pastoreo(ParteComun, FeitoPor, Base):
    __tablename__ = "pastoreo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    # Baleira mentres o gando segue no pasto
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)

    leiras: Mapped[list[PastoreoLeira]] = relationship(cascade="all, delete-orphan")
    animais: Mapped[list[PastoreoAnimal]] = relationship(cascade="all, delete-orphan")


class PastoreoLeira(Base):
    __tablename__ = "pastoreo_leira"

    id: Mapped[int] = mapped_column(primary_key=True)
    pastoreo_id: Mapped[int] = mapped_column(ForeignKey("pastoreo.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    # Superficie pastada; baleira = a do cultivo
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    # Catálogo tipo_cobertura_solo
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)


class PastoreoAnimal(Base):
    __tablename__ = "pastoreo_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    pastoreo_id: Mapped[int] = mapped_column(ForeignKey("pastoreo.id"), index=True)
    # Animais propios: o grupo. De terceiros: sen grupo, co REGA e a especie
    animal_id: Mapped[int | None] = mapped_column(ForeignKey("animal.id"), index=True,
                                                  default=None)
    rega: Mapped[str | None] = mapped_column(String(14), default=None)
    # Catálogo especie_animal
    especie_codigo: Mapped[str | None] = mapped_column(String(20), default=None)
    numero: Mapped[int] = mapped_column(Integer)
