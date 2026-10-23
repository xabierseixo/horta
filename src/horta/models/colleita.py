from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Colleita(Base):
    """Cada colleita dun cultivo (CUE bloque Cosecha) co seu lote. Baixa lóxica."""

    __tablename__ = "colleita"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    lote: Mapped[str] = mapped_column(String(40))
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    destino_colleita: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_restos: Mapped[str | None] = mapped_column(String(20), default=None)
    # Anexo V CUE 11 (colleita): respostas S/N obrigatorias e maquinaria (voluntaria)
    obten_sementes: Mapped[bool] = mapped_column(Boolean, default=False)
    obten_plantas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_colleita_ambiental: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    # Trazabilidade: quen apuntou a colleita
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
