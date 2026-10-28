"""Axuda para as migracións que pasan textos con persoas ou empresas de fóra a fichas de
persoa. Só a usan as
migracións de alembic/versions: traballa con SQL directo, sen os modelos, para que non
dependa de como sexan os modelos no futuro."""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.engine import Connection

_LETRAS_CIF = "ABCDEFGHJNPQRSUVW"


def e_cif(nif: str | None) -> bool:
    """O NIF é dunha entidade (CIF)?"""
    return bool(nif) and nif.strip().upper()[:1] in _LETRAS_CIF  # type: ignore[union-attr]


def persoa_para(conn: Connection, horta_id: int, papel: str | None, nome: str | None,
                **datos: Any) -> int:
    """A persoa ou entidade co mesmo NIF (ou co mesmo nome, se non hai NIF) nesa explotación,
    ou unha nova; queda co papel (se o ten). Os datos que lle faltaban complétanse."""
    datos = {k: (v.strip() if isinstance(v, str) else v) or None for k, v in datos.items()}
    nome = (nome or "").strip()[:200] or "Sen nome"
    if datos.get("nif"):
        fila = conn.execute(sa.text("SELECT id FROM persoa WHERE horta_id = :h AND nif = :n"),
                            {"h": horta_id, "n": datos["nif"]}).first()
    else:
        fila = conn.execute(sa.text(
            "SELECT id FROM persoa WHERE horta_id = :h AND lower(trim(nome)) = :n"),
            {"h": horta_id, "n": nome.lower()}).first()
    if fila is not None:
        persoa_id = int(fila.id)
        for campo, valor in datos.items():
            if valor is not None and campo != "tipo":
                conn.execute(sa.text(
                    f"UPDATE persoa SET {campo} = coalesce({campo}, :v) WHERE id = :i"),
                    {"v": valor, "i": persoa_id})
    else:
        datos["tipo"] = datos.get("tipo") or ("entidade" if e_cif(datos.get("nif")) else "persoa")
        campos = ", ".join(datos)
        valores = ", ".join(f":{c}" for c in datos)
        persoa_id = int(conn.execute(sa.text(
            f"INSERT INTO persoa (horta_id, nome, activa, discapacidade, {campos}) "
            f"VALUES (:horta_id, :nome, 1, 0, {valores})"),
            {"horta_id": horta_id, "nome": nome, **datos}).lastrowid)
    if papel is not None and not conn.execute(sa.text(
            "SELECT 1 FROM persoa_papel WHERE persoa_id = :i AND papel = :p"),
            {"i": persoa_id, "p": papel}).first():
        conn.execute(sa.text("INSERT INTO persoa_papel (persoa_id, papel) VALUES (:i, :p)"),
                     {"i": persoa_id, "p": papel})
    return persoa_id


def nome_de(conn: Connection, persoa_id: int | None) -> str | None:
    """Para as baixadas (downgrade): o nome da persoa, para volver ao texto."""
    if persoa_id is None:
        return None
    fila = conn.execute(sa.text("SELECT nome, nif, rega FROM persoa WHERE id = :i"),
                        {"i": persoa_id}).first()
    return fila.nome if fila else None


def pasar_a_persoas(conn: Connection, taboa: str, columna_id: str, papel: str | None,
                    consulta: str, nome: Any, datos: Any = lambda fila: {}) -> None:
    """Para cada fila de `consulta` (con `id`, `horta_id` e os textos), crea ou reutiliza a
    persoa (nome(fila), datos(fila)) co papel e gárdaa en `taboa.columna_id`. As filas sen
    ningún texto (nome(fila) None) quedan sen persoa."""
    for fila in conn.execute(sa.text(consulta)).mappings().all():
        texto = nome(fila)
        if not texto:
            continue
        persoa_id = persoa_para(conn, fila["horta_id"], papel, texto, **datos(fila))
        conn.execute(sa.text(f"UPDATE {taboa} SET {columna_id} = :p WHERE id = :i"),
                     {"p": persoa_id, "i": fila["id"]})


def primeiro(*textos: str | None) -> str | None:
    return next((t.strip() for t in textos if t and t.strip()), None)
