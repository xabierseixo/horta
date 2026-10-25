"""Rexistro de produtos fitosanitarios do MAPA (JSON de regfiweb) e pontes cos códigos SIEX."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class FitoProduto(Base):
    __tablename__ = "fito_produto"

    num_rexistro: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), index=True)
    titular: Mapped[str | None] = mapped_column(String(200), default=None)
    estado: Mapped[str | None] = mapped_column(String(20), default=None)
    data_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    data_cancelacion: Mapped[date | None] = mapped_column(Date, default=None)
    data_limite_venda: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class FitoMateria(Base):
    """Composición: substancia activa e concentración."""

    __tablename__ = "fito_materia"

    id: Mapped[int] = mapped_column(primary_key=True)
    num_rexistro: Mapped[str] = mapped_column(ForeignKey("fito_produto.num_rexistro"),
                                              index=True)
    sustancia: Mapped[str] = mapped_column(String(200))
    concentracion: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(40), default=None)


class FitoUso(Base):
    """Uso autorizado: cultivo × axente × dose × prazo de seguridade (etiqueta)."""

    __tablename__ = "fito_uso"

    id: Mapped[int] = mapped_column(primary_key=True)
    num_rexistro: Mapped[str] = mapped_column(ForeignKey("fito_produto.num_rexistro"),
                                              index=True)
    codigo_cultivo: Mapped[str] = mapped_column(String(16), index=True)
    cultivo: Mapped[str] = mapped_column(String(200))
    codigo_agente: Mapped[str] = mapped_column(String(30))
    agente: Mapped[str] = mapped_column(String(300))
    tipo_usuario: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_cultivo: Mapped[str | None] = mapped_column(String(40), default=None)
    dose_min: Mapped[float | None] = mapped_column(Float, default=None)
    dose_max: Mapped[float | None] = mapped_column(Float, default=None)
    unidade_dose: Mapped[str | None] = mapped_column(String(60), default=None)
    ps_tipo: Mapped[str] = mapped_column(String(20))
    ps_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    aplicacions_max: Mapped[int | None] = mapped_column(Integer, default=None)
    intervalo_min_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    condicionamento: Mapped[str | None] = mapped_column(String(2000), default=None)


class FitoPonteCultivo(Base):
    """Cultivo SIEX → cultivo do MAPA co mesmo código EPPO."""

    __tablename__ = "fito_ponte_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_siex_codigo: Mapped[int] = mapped_column(Integer, index=True)
    codigo_cultivo: Mapped[str] = mapped_column(String(16))


class FitoPonteAxente(Base):
    """Praga, enfermidade, mala herba ou regulador do SIEX → axente do MAPA (nome científico)."""

    __tablename__ = "fito_ponte_axente"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(20))
    codigo: Mapped[str] = mapped_column(String(20))
    codigo_agente: Mapped[str] = mapped_column(String(30), index=True)
