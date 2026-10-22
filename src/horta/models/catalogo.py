from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class CatalogoVersion(Base):
    """Unha importación dun ficheiro oficial de catálogo (FEGA)."""

    __tablename__ = "catalogo_version"
    __table_args__ = (UniqueConstraint("catalogo", "sha256"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60))
    nome_ficheiro: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    filas: Mapped[int] = mapped_column(Integer)
    data_importacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class CatalogoValor(Base):
    """Valor dun catálogo xenérico do SIEX (pragas, unidades, xustificacións...)."""

    __tablename__ = "catalogo_valor"
    __table_args__ = (UniqueConstraint("catalogo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
    descricion: Mapped[str] = mapped_column(String(500))
    codigo_eppo: Mapped[str | None] = mapped_column(String(12), default=None)
    categoria: Mapped[str | None] = mapped_column(String(120), default=None)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class CultivoSiex(Base):
    __tablename__ = "cultivo_siex"

    codigo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nome_oficial: Mapped[str] = mapped_column(String(200))
    nome_latin: Mapped[str | None] = mapped_column(String(200), default=None)
    codigo_eppo: Mapped[str | None] = mapped_column(String(12), default=None)
    codigo_upov: Mapped[str | None] = mapped_column(String(40), default=None)
    horticola: Mapped[bool] = mapped_column(Boolean, default=False)
    integrado: Mapped[bool] = mapped_column(Boolean, default=False)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class VariedadeSiex(Base):
    __tablename__ = "variedade_siex"
    __table_args__ = (UniqueConstraint("cultivo_codigo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_codigo: Mapped[int] = mapped_column(ForeignKey("cultivo_siex.codigo"), index=True)
    codigo: Mapped[int] = mapped_column(Integer)
    nome_oficial: Mapped[str] = mapped_column(String(300))
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class NomeGalego(Base):
    """Capa galega: nome en galego e prioridade de busca. Non a toca o importador."""

    __tablename__ = "nome_galego"
    __table_args__ = (UniqueConstraint("catalogo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60))
    codigo: Mapped[str] = mapped_column(String(20))
    nome_gl: Mapped[str] = mapped_column(String(200))
    prioridade: Mapped[int] = mapped_column(Integer, default=0)


class VariedadeLocal(Base):
    """Variedade tradicional galega que non está no catálogo do FEGA."""

    __tablename__ = "variedade_local"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_codigo: Mapped[int] = mapped_column(ForeignKey("cultivo_siex.codigo"))
    nome: Mapped[str] = mapped_column(String(200))
    fonte: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
