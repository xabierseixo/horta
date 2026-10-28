"""Coidado e saúde dos animais: cada coidado, enfermidade, cambio na produción, medicamento
ou visita dun grupo de animais (libro de rexistro gandeiro, RD 787/2023 anexo V 6, 7 e 11;
medicamentos, Reg. UE 2019/6 art. 108). Baixa lóxica."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class CoidadoAnimal(ParteComun, FeitoPor, ConMaquina, Base):
    __tablename__ = "coidado_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    # services.coidados_animais.TIPOS_COIDADO
    tipo: Mapped[str] = mapped_column(String(20))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Enfermidade, cambio na produción e medicamento: animais afectados ou tratados
    num_animais: Mapped[int | None] = mapped_column(Integer, default=None)
    identificacion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Medicamento
    medicamento: Mapped[str | None] = mapped_column(String(250), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
    veterinario_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    receita: Mapped[str | None] = mapped_column(String(50), default=None)
    tempo_espera_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    # Visita ou vehículo
    visitante_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    matricula: Mapped[str | None] = mapped_column(String(20), default=None)
