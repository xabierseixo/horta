"""Categorías dos contactos (deseño global §2bis): libres por explotación. As que trae a app
levan un `papel` (cliente, provedor...) porque o caderno e os formularios o usan: pódeselles
cambiar o nome, pero non borralas."""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String, Table, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base

# Contacto ↔ categoría libre (as que levan papel gárdanse en persoa_papel)
persoa_categoria = Table(
    "persoa_categoria", Base.metadata,
    Column("persoa_id", ForeignKey("persoa.id"), primary_key=True),
    Column("categoria_id", ForeignKey("categoria.id"), primary_key=True),
)


class Categoria(Base):
    __tablename__ = "categoria"
    __table_args__ = (UniqueConstraint("horta_id", "nome"), UniqueConstraint("horta_id", "papel"))

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(60))
    papel: Mapped[str | None] = mapped_column(String(20), default=None)
