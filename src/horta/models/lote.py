"""Lotes do produto que sae da explotación e as súas saídas (venda, casa, transformación,
perda, animais): o deseño. Nun lote entran
colleitas ou producións dos animais do mesmo produto; o que queda calcúlase."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class ProdutoVenda(Base):
    """Ficha do produto que sae: a categoría da venda
    directa, as clases e como se agrupa en lotes. Simétrica á ficha dos insumos (`produto`)."""

    __tablename__ = "produto_venda"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    unidade: Mapped[str] = mapped_column(String(20))
    # Que produto é: o cultivo oficial (colleitas) ou o produto animal
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    produto_animal: Mapped[str | None] = mapped_column(String(20), default=None)
    # Decreto 125/2014 anexo II (services.lotes.CATEGORIAS_VENDA_DIRECTA)
    categoria_venda_directa: Mapped[str | None] = mapped_column(String(20), default=None)
    # As clases da explotación para este produto, separadas por «;» (grande; mediana…)
    clases: Mapped[str | None] = mapped_column(String(500), default=None)
    # services.lotes.AGRUPACIONS: colleita, dia, semana, mes, man
    agrupacion: Mapped[str] = mapped_column(String(10), default="colleita")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


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
    produto_venda_id: Mapped[int] = mapped_column(ForeignKey("produto_venda.id"), index=True)
    # Se é de invernadoiro (máximos do Decreto 125/2014 anexo II)
    protexido: Mapped[bool] = mapped_column(Boolean, default=False)
    data: Mapped[date] = mapped_column(Date)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # Páxina pública do lote (xemelgo, paso 17): baleiro = non publicado
    token_publico: Mapped[str | None] = mapped_column(String(40), unique=True, default=None)


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
    # A clase que sae (grande, primeira…), se o lote se clasificou
    clase: Mapped[str | None] = mapped_column(String(60), default=None)
    # Cando se cobrou; baleira = pendente (paso 10, cartos)
    data_pago: Mapped[date | None] = mapped_column(Date, default=None)


class Clasificacion(ParteComun, FeitoPor, ConMaquina, Base):
    """Repartir un lote por clases: canto saíu de cada unha e o refugo (que conta como perda).
    O lote segue sendo o mesmo: a clase é un dato da partida."""

    __tablename__ = "clasificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    refugo: Mapped[float] = mapped_column(Float, default=0)
    clases: Mapped[list[ClasificacionClase]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")


class ClasificacionClase(Base):
    __tablename__ = "clasificacion_clase"

    id: Mapped[int] = mapped_column(primary_key=True)
    clasificacion_id: Mapped[int] = mapped_column(ForeignKey("clasificacion.id"), index=True)
    clase: Mapped[str] = mapped_column(String(60))
    # Na unidade do lote
    cantidade: Mapped[float] = mapped_column(Float)


class Mestura(ParteComun, FeitoPor, ConMaquina, Base):
    """Xuntar lotes xa feitos nun lote novo, que garda de onde vén e canto de cada un."""

    __tablename__ = "mestura"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    orixes: Mapped[list[MesturaOrixe]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")


class MesturaOrixe(Base):
    __tablename__ = "mestura_orixe"

    id: Mapped[int] = mapped_column(primary_key=True)
    mestura_id: Mapped[int] = mapped_column(ForeignKey("mestura.id"), index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    clase: Mapped[str | None] = mapped_column(String(60), default=None)
    # Na unidade do lote de orixe
    cantidade: Mapped[float] = mapped_column(Float)


class Transformacion(ParteComun, FeitoPor, ConMaquina, Base):
    """Elaborar un produto novo (conserva, queixo…) con lotes propios e ingredientes
    mercados: sae un lote novo que garda as súas orixes (paso 17)."""

    __tablename__ = "transformacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # O lote que sae e canto (na súa unidade)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    cantidade: Mapped[float] = mapped_column(Float)
    instalacion_id: Mapped[int | None] = mapped_column(ForeignKey("instalacion.id"),
                                                      default=None)
    entradas: Mapped[list[TransformacionEntrada]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")
    insumos: Mapped[list[TransformacionInsumo]] = relationship(
        cascade="all, delete-orphan", lazy="selectin")


class TransformacionEntrada(Base):
    """Un lote propio que entra na transformación (na unidade do lote)."""

    __tablename__ = "transformacion_entrada"

    id: Mapped[int] = mapped_column(primary_key=True)
    transformacion_id: Mapped[int] = mapped_column(ForeignKey("transformacion.id"),
                                                   index=True)
    lote_id: Mapped[int] = mapped_column(ForeignKey("lote.id"), index=True)
    clase: Mapped[str | None] = mapped_column(String(60), default=None)
    cantidade: Mapped[float] = mapped_column(Float)


class TransformacionInsumo(Base):
    """Un ingrediente ou envase mercado (na unidade do produto), e de que compra saíu."""

    __tablename__ = "transformacion_insumo"

    id: Mapped[int] = mapped_column(primary_key=True)
    transformacion_id: Mapped[int] = mapped_column(ForeignKey("transformacion.id"),
                                                   index=True)
    produto_id: Mapped[int] = mapped_column(ForeignKey("produto.id"))
    entrada_id: Mapped[int | None] = mapped_column(ForeignKey("entrada_produto.id"),
                                                   default=None)
    cantidade: Mapped[float] = mapped_column(Float)
