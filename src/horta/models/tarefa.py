from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Tarefa(Base):
    __tablename__ = "tarefa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"))
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    animal_id: Mapped[int | None] = mapped_column(ForeignKey("animal.id"), default=None)
    descricion: Mapped[str] = mapped_column(String(300))
    data: Mapped[date | None] = mapped_column(Date, default=None)
    data_limite: Mapped[date | None] = mapped_column(Date, default=None)
    data_feita: Mapped[date | None] = mapped_column(Date, default=None)
    prioridade: Mapped[str] = mapped_column(String(20), default="media")
    estado: Mapped[str] = mapped_column(String(20), default="pendente")
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    # Traballo por facer: o seu tipo (services.tarefas.TIPOS_TAREFA; baleiro = outro traballo)
    tipo: Mapped[str | None] = mapped_column(String(30), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    # Ao facela: o rexistro apuntado na táboa do seu tipo
    traballo_id: Mapped[int | None] = mapped_column(Integer, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
