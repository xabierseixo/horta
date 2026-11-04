"""Que dicirlle á persoa cando a base de datos rexeita un cambio (D2)."""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError


def mensaxe_integridade(erro: IntegrityError) -> str:
    """SQLite e PostgreSQL din o motivo en inglés; aquí tradúcese a algo que se entenda."""
    motivo = str(erro.orig).upper()
    if "FOREIGN KEY" in motivo:
        return "Non se pode: hai outros datos que dependen disto"
    if "UNIQUE" in motivo or "DUPLICATE" in motivo:
        return "Xa existe un rexistro con eses datos"
    return "Faltan datos ou algún non é válido"
