"""Documentos e certificacións da explotación (paso N2).

Gardar certificados e documentos da explotación ou de recursos concretos
(parcelas, cultivos, animais, máquinas, persoas, lotes ou instalacións), con
control de caducidade. O ficheiro físico gárdase fóra da base de datos
(services.documentos.cartafol_documentos); aquí gárdase só a referencia.
Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Documento(Base):
    __tablename__ = "documento"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(30))
    nome: Mapped[str] = mapped_column(String(200))
    emisor: Mapped[str | None] = mapped_column(String(200), default=None)
    numero: Mapped[str | None] = mapped_column(String(100), default=None)
    data_emision: Mapped[date | None] = mapped_column(Date, default=None)
    data_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    que: Mapped[str | None] = mapped_column(String(30), default=None)
    ref_id: Mapped[int | None] = mapped_column(Integer, default=None)
    ficheiro: Mapped[str | None] = mapped_column(String(60), default=None)
    nome_orixinal: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(Text, default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
