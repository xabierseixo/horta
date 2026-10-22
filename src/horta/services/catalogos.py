# src/horta/services/catalogos.py
from __future__ import annotations

import csv
import unicodedata
from datetime import date
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CultivoSiex, NomeGalego
from horta.services.errors import OperacionNonPermitidaError


def normalizar(texto: str) -> str:
    sen_acentos = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in sen_acentos if not unicodedata.combining(c))


def _vixente(na_data: date):
    return or_(CatalogoValor.data_baixa.is_(None), CatalogoValor.data_baixa > na_data)


def valores_vixentes(
    session: Session, catalogo: str, na_data: date | None = None
) -> list[CatalogoValor]:
    na_data = na_data or date.today()
    valores = (
        session.query(CatalogoValor)
        .filter(CatalogoValor.catalogo == catalogo, _vixente(na_data))
        .all()
    )
    return sorted(valores, key=lambda v: (len(v.codigo), v.codigo))


def validar_codigo(session: Session, catalogo: str, codigo: str, na_data: date) -> CatalogoValor:
    valor = (
        session.query(CatalogoValor)
        .filter(CatalogoValor.catalogo == catalogo, CatalogoValor.codigo == codigo,
                _vixente(na_data))
        .first()
    )
    if valor is None:
        raise OperacionNonPermitidaError(
            f"O código {codigo} non existe ou está de baixa no catálogo {catalogo}"
        )
    return valor


def describir(session: Session, catalogo: str, codigo: str) -> str:
    valor = session.query(CatalogoValor).filter_by(catalogo=catalogo, codigo=codigo).first()
    return valor.descricion if valor else codigo


def buscar_cultivos(
    session: Session, texto: str, limite: int = 20
) -> list[tuple[CultivoSiex, str]]:
    nomes = {
        int(n.codigo): (n.nome_gl, n.prioridade)
        for n in session.query(NomeGalego).filter_by(catalogo="cultivo")
    }
    buscado = normalizar(texto)
    resultado: list[tuple[int, str, CultivoSiex]] = []
    for cultivo in session.query(CultivoSiex).filter(CultivoSiex.data_baixa.is_(None)):
        nome_gl, prioridade = nomes.get(cultivo.codigo, (None, 0))
        nome = nome_gl or cultivo.nome_oficial.capitalize()
        candidatos = [normalizar(nome), normalizar(cultivo.nome_oficial)]
        if not buscado or any(buscado in c for c in candidatos):
            resultado.append((-prioridade, normalizar(nome), cultivo))
    resultado.sort(key=lambda r: (r[0], r[1]))
    return [(c, nomes.get(c.codigo, (None, 0))[0] or c.nome_oficial.capitalize())
            for _, _, c in resultado[:limite]]


def cargar_nomes_galegos(session: Session, ruta: Path) -> int:
    """Carga/actualiza nomes galegos de cultivos dende un CSV `codigo;nome_gl;prioridade`."""
    contador = 0
    with ruta.open(encoding="utf-8") as ficheiro:
        for fila in csv.DictReader(ficheiro, delimiter=";"):
            codigo = fila["codigo"].strip()
            nome = session.query(NomeGalego).filter_by(catalogo="cultivo", codigo=codigo).first()
            if nome is None:
                nome = NomeGalego(catalogo="cultivo", codigo=codigo)
                session.add(nome)
            nome.nome_gl = fila["nome_gl"].strip()
            nome.prioridade = int(fila["prioridade"])
            contador += 1
    session.commit()
    return contador
