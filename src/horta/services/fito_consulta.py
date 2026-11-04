"""Consultas ao rexistro do MAPA: buscar produtos e comprobar o uso nun tratamento.

A comprobación só avisa, nunca bloquea: a etiqueta é a referencia legal, as pontes cos
códigos SIEX non cobren todo e as etiquetas teñen períodos de graza ao cambiar.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.horta import Horta
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.services.catalogos import describir
from horta.services.tratamentos_fito import DatosTratamento

INFO, AVISO, FORTE = "info", "aviso", "forte"
_VIXENTE = "Vigente"


@dataclass
class Aviso:
    nivel: str
    texto: str


def buscar_produtos(session: Session, texto: str, limite: int = 20) -> list[FitoProduto]:
    """Produtos do rexistro polo nome comercial ou o nº de rexistro."""
    texto = texto.strip()
    if len(texto) < 2:
        return []
    patron = f"%{texto}%"
    return list(session.query(FitoProduto)
                .filter(or_(FitoProduto.nome.ilike(patron),
                            FitoProduto.num_rexistro.ilike(patron)))
                .order_by(FitoProduto.nome).limit(limite))


def materia_activa(session: Session, num_rexistro: str) -> str:
    """'AZUFRE 80 % p/p + COBRE 20 %' para encher o campo do tratamento."""
    partes = []
    for m in session.query(FitoMateria).filter_by(num_rexistro=num_rexistro):
        cantidade = f" {m.concentracion:g}" if m.concentracion is not None else ""
        partes.append(f"{m.sustancia}{cantidade} {m.unidade or ''}".strip())
    return " + ".join(partes)


def nomes_comuns_problemas(session: Session, catalogo: str) -> dict[str, list[str]]:
    """Para cada código SIEX dun tipo de problema, os nomes comúns no rexistro do MAPA."""
    comuns: dict[str, list[str]] = {}
    filas = (
        session.query(FitoPonteAxente.codigo, FitoUso.agente)
        .join(FitoUso, FitoUso.codigo_agente == FitoPonteAxente.codigo_agente)
        .filter(FitoPonteAxente.catalogo == catalogo)
        .distinct()
        .order_by(FitoUso.agente)
    )
    for codigo, agente in filas:
        nome = agente.split(",")[0].strip()
        if not nome:
            continue
        nomes = comuns.setdefault(codigo, [])
        if nome not in nomes:
            nomes.append(nome)
    return comuns


def etiqueta_problema(cientifico: str, nomes_comuns: list[str]) -> str:
    """«Nome común — Nome científico» (ata dous nomes separados por « / ») ou só o científico."""
    if not nomes_comuns:
        return cientifico
    return f"{' / '.join(nomes_comuns[:2])} — {cientifico}"


def _prefixo(codigo: str) -> str:
    grupos = [codigo[i:i + 2] for i in range(0, 16, 2)]
    while grupos and grupos[-1] == "00":
        grupos.pop()
    return "".join(grupos)


def _con_superiores_cultivo(atopados: set[str], todos: set[str]) -> set[str]:
    """Inclúe as categorías superiores: Patata → Hortalizas → Cultivos agrícolas…"""
    return atopados | {s for s in todos if any(c != s and c.startswith(_prefixo(s))
                                               for c in atopados)}


def _con_superiores_axente(atopados: set[str], todos: set[str]) -> set[str]:
    return atopados | {s for s in todos if any(c.startswith(s + ".") for c in atopados)}


def _cultivos_mapa(session: Session, cultivo: Cultivo, usos: list[FitoUso]) -> set[str]:
    if cultivo.cultivo_siex_codigo is None:
        return set()
    atopados = {p.codigo_cultivo for p in session.query(FitoPonteCultivo)
                .filter_by(cultivo_siex_codigo=cultivo.cultivo_siex_codigo)}
    return _con_superiores_cultivo(atopados, {u.codigo_cultivo for u in usos}) if atopados \
        else set()


def _axentes_mapa(session: Session, datos: DatosTratamento, usos: list[FitoUso]) -> set[str]:
    atopados: set[str] = set()
    for p in datos.problemas:
        atopados |= {a.codigo_agente for a in session.query(FitoPonteAxente)
                     .filter_by(catalogo=p.tipo, codigo=p.codigo)}
    return _con_superiores_axente(atopados, {u.codigo_agente for u in usos}) if atopados \
        else set()


def _unidade(texto: str | None) -> str:
    return (texto or "").lower().replace("cc", "ml").replace(" ", "")


def _num(x: float) -> str:
    return f"{x:g}".replace(".", ",")


def _dose_uso(u: FitoUso) -> str:
    if u.dose_max is None:
        return ""
    dose = (_num(u.dose_max) if u.dose_min in (None, u.dose_max)
            else f"{_num(u.dose_min)}–{_num(u.dose_max)}")
    return f"{dose} {u.unidade_dose or ''}".strip()


def _resumo_uso(u: FitoUso) -> str:
    partes = []
    if dose := _dose_uso(u):
        partes.append(dose)
    if u.ps_tipo == "non_procede":
        partes.append("sen prazo de seguridade")
    elif u.ps_dias is not None:
        partes.append(f"prazo de seguridade {u.ps_dias} días")
    if u.aplicacions_max:
        partes.append(f"máx. {u.aplicacions_max} aplicacións")
    return ", ".join(partes)


def dose_etiqueta(session: Session, num_rexistro: str | None, cultivo_id: int | None) -> str:
    """Resumo da dose da etiqueta do produto para o cultivo indicado."""
    if not num_rexistro or cultivo_id is None:
        return ""
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        return ""
    todos = list(session.query(FitoUso).filter_by(num_rexistro=num_rexistro.strip()))
    codigos = _cultivos_mapa(session, cultivo, todos)
    usos = [u for u in todos if u.codigo_cultivo in codigos]
    resumos = list(dict.fromkeys(_resumo_uso(u) for u in usos if _resumo_uso(u)))
    return f"Dose na etiqueta ({cultivo.especie}): {' · '.join(resumos)}" if resumos else ""


def _aplicacions_previas(session: Session, num_rexistro: str, cultivo_ids: list[int],
                         excluir_id: int | None) -> int:
    consulta = (session.query(TratamentoFito.id)
                .join(TratamentoProduto, TratamentoProduto.tratamento_id == TratamentoFito.id)
                .join(TratamentoCultivo, TratamentoCultivo.tratamento_id == TratamentoFito.id)
                .filter(TratamentoFito.baixa.is_(False),
                        TratamentoProduto.num_rexistro == num_rexistro,
                        TratamentoCultivo.cultivo_id.in_(cultivo_ids)))
    if excluir_id is not None:
        consulta = consulta.filter(TratamentoFito.id != excluir_id)
    return consulta.distinct().count()


def comprobar_tratamento(session: Session, horta: Horta, datos: DatosTratamento,
                         tratamento_id: int | None = None) -> list[Aviso]:
    avisos: list[Aviso] = []
    cultivo = session.get(Cultivo, datos.cultivos[0].cultivo_id) if datos.cultivos else None
    cultivo_ids = [c.cultivo_id for c in datos.cultivos]
    for linha in datos.produtos:
        if not linha.num_rexistro:
            continue
        produto = session.get(FitoProduto, linha.num_rexistro.strip())
        nome = linha.nome_comercial or linha.num_rexistro
        if produto is None:
            avisos.append(Aviso(FORTE, f"{nome}: o nº de rexistro {linha.num_rexistro} non "
                                       "figura no rexistro do MAPA."))
            continue
        nome = produto.nome
        if produto.estado != _VIXENTE:
            cando = (f" o {produto.data_cancelacion:%d/%m/%Y}" if produto.data_cancelacion
                     else "")
            venda = (f"; límite de venda {produto.data_limite_venda:%d/%m/%Y}"
                     if produto.data_limite_venda else "")
            avisos.append(Aviso(FORTE, f"{nome}: cancelado no rexistro{cando}{venda}. "
                                       "Comproba o prazo de uso."))
        elif produto.data_caducidade and produto.data_caducidade < datos.data_inicio:
            avisos.append(Aviso(FORTE, f"{nome}: a autorización caducou o "
                                       f"{produto.data_caducidade:%d/%m/%Y}."))
        if cultivo is None:
            continue
        todos = list(session.query(FitoUso).filter_by(num_rexistro=produto.num_rexistro))
        codigos = _cultivos_mapa(session, cultivo, todos)
        if not codigos:
            avisos.append(Aviso(INFO, f"{nome}: non podemos comprobar automaticamente o uso en "
                                      f"{cultivo.especie}. Mira a etiqueta."))
            continue
        usos = [u for u in todos if u.codigo_cultivo in codigos]
        if not usos:
            avisos.append(Aviso(FORTE, f"{nome}: non está autorizado en {cultivo.especie} "
                                       "segundo o rexistro do MAPA."))
            continue
        axentes = _axentes_mapa(session, datos, usos)
        validos = [u for u in usos if u.codigo_agente in axentes]
        if not axentes:
            avisos.append(Aviso(INFO, f"{nome}: autorizado en {cultivo.especie}; non podemos "
                                      "comprobar o problema automaticamente. Mira a etiqueta."))
            validos = usos
        elif not validos:
            problemas = ", ".join(describir(session, p.tipo, p.codigo) for p in datos.problemas)
            autorizados = sorted({u.agente.split(",")[0] for u in usos})
            lista = ", ".join(autorizados[:8]) + ("…" if len(autorizados) > 8 else "")
            avisos.append(Aviso(FORTE, f"{nome}: autorizado en {cultivo.especie}, pero non "
                                       f"atopamos o uso contra {problemas}. Autorizado contra: "
                                       f"{lista}."))
            continue
        else:
            u = validos[0]
            avisos.append(Aviso(INFO, f"{nome}: autorizado contra {u.agente.split(',')[0]}: "
                                      f"{_resumo_uso(u)}."))
        if not horta.uso_profesional and all(u.tipo_usuario == "Profesional" for u in validos):
            avisos.append(Aviso(AVISO, f"{nome}: produto só para usuarios profesionais "
                                       "(carné ROPO)."))
        unidade = _unidade(describir(session, "unidade_medida", linha.unidade))
        maximos = [u.dose_max for u in validos
                   if u.dose_max is not None and _unidade(u.unidade_dose) == unidade]
        if maximos:
            if linha.dose is not None and linha.dose > max(maximos):
                avisos.append(Aviso(FORTE, f"{nome}: a dose ({_num(linha.dose)}) pasa da máxima "
                                           f"da etiqueta ({_num(max(maximos))} {unidade})."))
        elif con_dose := [u for u in validos if u.dose_max is not None and u.unidade_dose]:
            u_dose = con_dose[0]
            avisos.append(Aviso(
                AVISO,
                f"{nome}: a etiqueta dá a dose en {u_dose.unidade_dose} ({_dose_uso(u_dose)}): "
                "non se pode comprobar a dose máxima. No caderno apúntanse os kg/ha ou L/ha "
                "botados.",
            ))
        limites = [u.aplicacions_max for u in validos if u.aplicacions_max]
        if limites:
            feitas = _aplicacions_previas(session, produto.num_rexistro, cultivo_ids,
                                          tratamento_id) + 1
            if feitas > max(limites):
                avisos.append(Aviso(FORTE, f"{nome}: esta sería a aplicación nº {feitas} neste "
                                           f"cultivo; a etiqueta permite {max(limites)}."))
    return avisos


def prazo_seguridade(session: Session, tratamento: TratamentoFito) -> date | None:
    """Primeiro día en que se pode colleitar: fin do tratamento + o prazo máis longo."""
    cultivo = (session.get(Cultivo, tratamento.cultivos[0].cultivo_id)
               if tratamento.cultivos else None)
    dias: list[int] = []
    for linha in tratamento.produtos:
        if not linha.num_rexistro:
            continue
        usos = list(session.query(FitoUso).filter_by(num_rexistro=linha.num_rexistro))
        codigos = _cultivos_mapa(session, cultivo, usos) if cultivo else set()
        dias += [u.ps_dias for u in usos
                 if u.ps_dias and (not codigos or u.codigo_cultivo in codigos)]
    return tratamento.data_fin + timedelta(days=max(dias)) if dias else None


def aviso_prazo_colleita(session: Session, cultivo_id: int, data: date) -> str | None:
    """Aviso se se colleita antes de que remate o prazo de seguridade dalgún tratamento."""
    tratamentos = (session.query(TratamentoFito)
                   .join(TratamentoCultivo, TratamentoCultivo.tratamento_id == TratamentoFito.id)
                   .filter(TratamentoFito.baixa.is_(False),
                           TratamentoCultivo.cultivo_id == cultivo_id,
                           TratamentoFito.data_fin <= data)
                   .order_by(TratamentoFito.data_fin))
    pendentes = [(prazo, t) for t in tratamentos
                 if (prazo := prazo_seguridade(session, t)) is not None and data < prazo]
    if not pendentes:
        return None
    prazo, t = max(pendentes, key=lambda par: par[0])
    produtos = ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
    return (f"Ollo: o tratamento do {t.data_fin:%d/%m/%Y} ({produtos}) ten prazo de "
            f"seguridade: non se debería colleitar antes do {prazo:%d/%m/%Y}.")
