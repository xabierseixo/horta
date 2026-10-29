"""Outros gastos e ingresos: os que non saen das compras nin das vendas (seguros, aluguer,
auga, luz, cotas, axudas…). o deseño. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ApunteCartos(Base):
    __tablename__ = "apunte_cartos"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # gasto ou ingreso
    tipo: Mapped[str] = mapped_column(String(10))
    # services.cartos.CATEGORIAS
    categoria: Mapped[str] = mapped_column(String(20))
    concepto: Mapped[str] = mapped_column(String(200))
    data: Mapped[date] = mapped_column(Date)
    importe: Mapped[float] = mapped_column(Float)
    # A quen se paga ou quen paga
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    # Cando se cobrou ou pagou; baleira = pendente
    data_pago: Mapped[date | None] = mapped_column(Date, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
