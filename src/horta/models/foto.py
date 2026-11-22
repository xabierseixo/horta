"""Fotos dos traballos, parcelas, animais e lotes (paso 11a). O ficheiro gárdase fóra da BD
(services.fotos.cartafol_fotos); aquí só a referencia. Baixa lóxica: a foto é unha evidencia."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Foto(Base):
    __tablename__ = "foto"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # A que vai: un tipo do Diario (services.diario.TIPOS) ou parcela, animal, lote
    que: Mapped[str] = mapped_column(String(30))
    ref_id: Mapped[int] = mapped_column(Integer)
    # Nome do ficheiro dentro do cartafol da explotación
    ficheiro: Mapped[str] = mapped_column(String(60))
    nome_orixinal: Mapped[str | None] = mapped_column(String(200), default=None)
    data: Mapped[date] = mapped_column(Date)
    nota: Mapped[str | None] = mapped_column(String(300), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
