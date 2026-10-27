"""Coidado e saúde dos animais: cada coidado, enfermidade, cambio na produción, medicamento
ou visita dun grupo de animais (libro de rexistro gandeiro, RD 787/2023 anexo V 6, 7 e 11;
medicamentos, Reg. UE 2019/6 art. 108). Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class CoidadoAnimal(Base):
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
    provedor: Mapped[str | None] = mapped_column(String(300), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
    veterinario: Mapped[str | None] = mapped_column(String(200), default=None)
    receita: Mapped[str | None] = mapped_column(String(50), default=None)
    tempo_espera_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    # Visita ou vehículo
    visitante: Mapped[str | None] = mapped_column(String(200), default=None)
    matricula: Mapped[str | None] = mapped_column(String(20), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
