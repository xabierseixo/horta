"""Lotes do produto que sae da explotación e as súas saídas (venda, casa, transformación,
perda, animais): o deseño. Nun lote entran
colleitas ou producións dos animais do mesmo produto; o que queda calcúlase."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Lote(Base):
    __tablename__ = "lote"
    __table_args__ = (UniqueConstraint("horta_id", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    # Trazabilidade (Reg. CE 178/2002 art. 18): AAAA-PRODUTO-NNN, único na explotación
    codigo: Mapped[str] = mapped_column(String(40))
    produto: Mapped[str] = mapped_column(String(120))
    # Que produto é: o cultivo oficial (colleitas) ou o produto animal (services.producions_animais)
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    produto_animal: Mapped[str | None] = mapped_column(String(20), default=None)
    unidade: Mapped[str] = mapped_column(String(20))
    # Decreto 125/2014 anexo II (services.lotes.CATEGORIAS_VENDA_DIRECTA) e se é de invernadoiro
    categoria_venda_directa: Mapped[str | None] = mapped_column(String(20), default=None)
    protexido: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[date] = mapped_column(Date)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)


class LoteSaida(ParteComun, FeitoPor, ConMaquina, Base):
    """Cada saída dun lote: un traballo coa parte común."""

    __tablename__ = "lote_saida"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    # services.lotes.TIPOS_SAIDA: venda, casa, transformacion, perda, animais
    tipo: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    # Só nas vendas (Decreto 125/2014 art. 6; CUE 3)
    canle: Mapped[str | None] = mapped_column(String(20), default=None)
    lugar: Mapped[str | None] = mapped_column(String(200), default=None)
    comprador_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    importe: Mapped[float | None] = mapped_column(Float, default=None)
