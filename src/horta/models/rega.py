"""Rega (CUE bloque 10): cada rega, nunha ou varias leiras. Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Rega(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "rega"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    sistema_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)

    boas_practicas: Mapped[list[RegaBoaPractica]] = relationship(cascade="all, delete-orphan")
    # As leiras (cultivos) onde se fixo: unha ou varias
    #
    leiras: Mapped[list[RegaCultivo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )

    # Transición (tarefa 084): a primeira leira, mentres se adaptan os informes e as pantallas
    @property
    def cultivo_id(self) -> int:
        return self.leiras[0].cultivo_id

    @property
    def superficie_ha(self) -> float | None:
        return self.leiras[0].superficie_ha


class RegaBoaPractica(Base):
    __tablename__ = "rega_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class RegaCultivo(Base):
    """Cada leira (cultivo) dunha rega, coa superficie onde se fixo."""

    __tablename__ = "rega_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    rega_id: Mapped[int] = mapped_column(ForeignKey("rega.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
