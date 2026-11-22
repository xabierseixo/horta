# Tarefa 071 — Tratamentos: buscar produtos e comprobar o uso no rexistro do MAPA

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 070c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Servizo que busca produtos no rexistro, dá a materia activa e comproba un tratamento: autorizado ou non no cultivo e para o problema, dose máxima, nº de aplicacións, uso profesional, produto cancelado e prazo de seguridade (tamén para avisar nas colleitas). Só avisa, non bloquea. Probado en seco co rexistro real. Deseño: `docs/superpowers/specs/2026-10-25-tratamentos-completos-design.md` §2–3.

## Ficheiros a tocar

- `src/horta/services/fito_consulta.py` (**ficheiro novo**)
- `tests/services/test_fito_consulta.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/fito_consulta.py`

Contido completo:
```python
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


def _resumo_uso(u: FitoUso) -> str:
    partes = []
    if u.dose_max is not None:
        dose = (_num(u.dose_max) if u.dose_min in (None, u.dose_max)
                else f"{_num(u.dose_min)}–{_num(u.dose_max)}")
        partes.append(f"{dose} {u.unidade_dose or ''}".strip())
    if u.ps_tipo == "non_procede":
        partes.append("sen prazo de seguridade")
    elif u.ps_dias is not None:
        partes.append(f"prazo de seguridade {u.ps_dias} días")
    if u.aplicacions_max:
        partes.append(f"máx. {u.aplicacions_max} aplicacións")
    return ", ".join(partes)


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
        if linha.dose is not None and maximos and linha.dose > max(maximos):
            avisos.append(Aviso(FORTE, f"{nome}: a dose ({_num(linha.dose)}) pasa da máxima da "
                                       f"etiqueta ({_num(max(maximos))} {unidade})."))
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
    for t in tratamentos:
        prazo = prazo_seguridade(session, t)
        if prazo is not None and data < prazo:
            produtos = ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
            return (f"Ollo: o tratamento do {t.data_fin:%d/%m/%Y} ({produtos}) ten prazo de "
                    f"seguridade: non se debería colleitar antes do {prazo:%d/%m/%Y}.")
    return None
```

### Paso 2 — crear o ficheiro `tests/services/test_fito_consulta.py`

Contido completo:
```python
from datetime import date

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex
from horta.models.cultivo import Cultivo
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.services.fito_consulta import (
    AVISO,
    FORTE,
    INFO,
    aviso_prazo_colleita,
    buscar_produtos,
    comprobar_tratamento,
    materia_activa,
    prazo_seguridade,
)
from horta.services.tratamentos_fito import DatosTratamento, LinhaCultivo, LinhaProduto, Problema

D = date(2026, 6, 1)
PATATA, HORTALIZAS = "0102090000000000", "0102000000000000"
MILDIU = "8.48.4.5"


def _uso(num, cultivo, agente, nome, **extra):
    datos = dict(num_rexistro=num, codigo_cultivo=cultivo, cultivo="c", codigo_agente=agente,
                 agente=nome, tipo_usuario="Profesional", dose_min=0.5, dose_max=1.0,
                 unidade_dose="l/ha", ps_tipo="dias", ps_dias=14, aplicacions_max=2)
    datos.update(extra)
    return FitoUso(**datos)


def _escenario(session, profesional=True, siex=True):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", codigo_eppo="SOLTU",
                            version_id=v.id))
    for catalogo, codigo, texto in [("enfermidade", "77", "Phytophthora infestans"),
                                    ("enfermidade", "78", "Botrytis cinerea"),
                                    ("unidade_medida", "18", "L/ha")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=texto,
                                  version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-1", nome="MILDIUCIDA", estado="Vigente",
                            version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-2", nome="XERAL", estado="Vigente",
                            version_id=v.id))
    session.add(FitoProduto(num_rexistro="ES-3", nome="VELLO", estado="Cancelado",
                            data_cancelacion=date(2025, 1, 1), version_id=v.id))
    session.flush()
    session.add(FitoMateria(num_rexistro="ES-1", sustancia="COBRE", concentracion=20,
                            unidade="% p/p"))
    session.add(_uso("ES-1", PATATA, MILDIU, "Mildiu de la patata, Phytophthora infestans"))
    session.add(_uso("ES-2", HORTALIZAS, "8.48", "Mildius, Peronosporaceae", ps_dias=3))
    session.add(FitoPonteCultivo(cultivo_siex_codigo=99, codigo_cultivo=PATATA))
    session.add(FitoPonteAxente(catalogo="enfermidade", codigo="77", codigo_agente=MILDIU))
    session.add(FitoPonteAxente(catalogo="enfermidade", codigo="78", codigo_agente="8.20.1"))
    horta = Horta(nome="H", uso_profesional=profesional)
    session.add(horta)
    session.flush()
    parcela = Parcela(horta_id=horta.id, nome="P", estado="activa")
    session.add(parcela)
    session.flush()
    cultivo = Cultivo(parcela_id=parcela.id, especie="Pataca", estado="en_curso",
                      cultivo_siex_codigo=99 if siex else None)
    session.add(cultivo)
    session.commit()
    return horta, cultivo


def _datos(cultivo, num="ES-1", problema="77", dose=1.0):
    return DatosTratamento(
        data_inicio=D, data_fin=D, cultivos=[LinhaCultivo(cultivo.id, None)],
        problemas=[Problema("enfermidade", problema)], xustificacions=[],
        produtos=[LinhaProduto(tipo_produto="1", unidade="18", num_rexistro=num, dose=dose)],
    )


def _textos(avisos, nivel):
    return " | ".join(a.texto for a in avisos if a.nivel == nivel)


def test_uso_autorizado_informa_da_etiqueta(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "autorizado contra Mildiu de la patata" in _textos(avisos, INFO)
    assert "prazo de seguridade 14 días" in _textos(avisos, INFO)
    assert not _textos(avisos, FORTE)


def test_problema_non_autorizado(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, problema="78"))
    assert "non atopamos o uso contra Botrytis cinerea" in _textos(avisos, FORTE)


def test_categorias_superiores_do_cultivo_e_do_problema(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, num="ES-2"))
    assert "XERAL: autorizado contra Mildius" in _textos(avisos, INFO)


def test_problema_sen_ponte(session):
    horta, cultivo = _escenario(session)
    datos = _datos(cultivo)
    datos.problemas = [Problema("enfermidade", "79")]
    avisos = comprobar_tratamento(session, horta, datos)
    assert "non podemos comprobar o problema" in _textos(avisos, INFO)


def test_cultivo_sen_codigo_siex(session):
    horta, cultivo = _escenario(session, siex=False)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "non podemos comprobar automaticamente o uso" in _textos(avisos, INFO)


def test_dose_por_riba_da_maxima(session):
    horta, cultivo = _escenario(session)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo, dose=1.5))
    assert "pasa da máxima da etiqueta (1 l/ha)" in _textos(avisos, FORTE)


def test_autoconsumo_e_produto_profesional(session):
    horta, cultivo = _escenario(session, profesional=False)
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "só para usuarios profesionais" in _textos(avisos, AVISO)


def test_produto_cancelado_ou_descoñecido(session):
    horta, cultivo = _escenario(session)
    assert "cancelado no rexistro o 01/01/2025" in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo, num="ES-3")), FORTE)
    assert "non figura no rexistro" in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo, num="ES-9")), FORTE)


def test_maximo_de_aplicacions(session):
    horta, cultivo = _escenario(session)
    for _ in range(2):
        t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
        t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
        t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1")]
        session.add(t)
    session.commit()
    avisos = comprobar_tratamento(session, horta, _datos(cultivo))
    assert "aplicación nº 3" in _textos(avisos, FORTE)
    # Ao editar un dos dous xa gardados non conta el mesmo
    assert "aplicación nº" not in _textos(
        comprobar_tratamento(session, horta, _datos(cultivo), tratamento_id=t.id), FORTE)


def test_prazo_seguridade(session):
    horta, cultivo = _escenario(session)
    t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1"),
                  TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-2")]
    session.add(t)
    session.commit()
    assert prazo_seguridade(session, t) == date(2026, 6, 15)


def test_buscar_e_materia_activa(session):
    _escenario(session)
    assert [p.num_rexistro for p in buscar_produtos(session, "mildi")] == ["ES-1"]
    assert [p.nome for p in buscar_produtos(session, "ES-2")] == ["XERAL"]
    assert buscar_produtos(session, "m") == []
    assert materia_activa(session, "ES-1") == "COBRE 20 % p/p"


def test_aviso_prazo_colleita(session):
    horta, cultivo = _escenario(session)
    t = TratamentoFito(horta_id=horta.id, data_inicio=D, data_fin=D)
    t.cultivos = [TratamentoCultivo(cultivo_id=cultivo.id)]
    t.produtos = [TratamentoProduto(tipo_produto="1", unidade="18", num_rexistro="ES-1",
                                    nome_comercial="MILDIUCIDA")]
    session.add(t)
    session.commit()
    aviso = aviso_prazo_colleita(session, cultivo.id, date(2026, 6, 10))
    assert aviso and "MILDIUCIDA" in aviso and "15/06/2026" in aviso
    assert aviso_prazo_colleita(session, cultivo.id, date(2026, 6, 15)) is None
    assert aviso_prazo_colleita(session, cultivo.id, date(2026, 5, 1)) is None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existe services/fito_consulta.py coas súas probas.
