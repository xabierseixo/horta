# Tarefa 030 — Servizo de colleitas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 029 (modelo `Colleita` e campos novos do cultivo).

## Obxectivo

Lóxica das colleitas segundo `docs/superpowers/specs/2026-10-23-cultivo-e-colleitas-design.md` §2: crear, modificar, dar de baixa e listar colleitas; propor un lote libre; calcular o rendemento en kg/ha. Ademais, `actualizar_cultivo` debe aceptar os campos novos (superficie_ha, data_inicio...) e non se pode borrar un cultivo con colleitas.

## Ficheiros a tocar

- `src/horta/services/colleitas.py` (**ficheiro novo**)
- `tests/services/test_colleitas.py` (**ficheiro novo**)
- `src/horta/services/cultivos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/colleitas.py`

Contido completo:

```python
"""Colleitas dos cultivos (CUE bloque Cosecha), cada unha co seu lote. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

UNIDADES_COLLEITA = ("kg", "t", "unidades", "ducias", "mazos", "litros")
_A_KG = {"kg": 1.0, "t": 1000.0}
# Anexo V CUE campo 516: finalidade só con destino "Vinificación" (22) ou "Outro procesamento"
_DESTINOS_CON_FINALIDADE = ("22", "23")


@dataclass
class DatosColleita:
    cultivo_id: int
    data: date
    cantidade: float
    unidade: str
    lote: str
    superficie_ha: float | None = None
    destino_colleita: str | None = None
    destino_restos: str | None = None
    notas: str | None = None
    data_fin: date | None = None
    albaran_factura: str | None = None
    obten_sementes: bool = False
    obten_plantas: bool = False
    sen_colleita_ambiental: bool = False
    restos_no_solo: bool = False
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h_ha: float | None = None


def _cultivo_e_horta(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    return cultivo, horta_id


def _lotes_da_horta(session: Session, horta_id: int, excepto_id: int | None = None) -> set[str]:
    consulta = (
        session.query(Colleita.lote)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if excepto_id is not None:
        consulta = consulta.filter(Colleita.id != excepto_id)
    return {lote for (lote,) in consulta}


def _validar(
    session: Session,
    datos: DatosColleita,
    cultivo: Cultivo,
    horta_id: int,
    hoxe: date,
    excepto_id: int | None = None,
) -> None:
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if datos.unidade not in UNIDADES_COLLEITA:
        raise OperacionNonPermitidaError(f"Unidade non válida: {datos.unidade}")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data da colleita non pode ser futura")
    if cultivo.data_inicio is not None and datos.data < cultivo.data_inicio:
        raise OperacionNonPermitidaError("A colleita non pode ser anterior ao inicio do cultivo")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie colleitada é maior ca do cultivo")
    lote = datos.lote.strip()
    if not lote:
        raise OperacionNonPermitidaError("O lote é obrigatorio")
    if lote in _lotes_da_horta(session, horta_id, excepto_id):
        raise OperacionNonPermitidaError(f"O lote {lote} xa existe nesta explotación")
    if datos.data_fin is not None and datos.data_fin < datos.data:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.destino_colleita:
        if cultivo.destino not in _DESTINOS_CON_FINALIDADE:
            raise OperacionNonPermitidaError(
                "A finalidade só se indica se o cultivo vai a viño ou a procesado industrial"
            )
        validar_codigo(session, "destino_colleita", datos.destino_colleita, datos.data)
    if datos.destino_restos:
        validar_codigo(session, "destino_restos", datos.destino_restos, datos.data)


def _copiar(colleita: Colleita, datos: DatosColleita) -> None:
    colleita.cultivo_id = datos.cultivo_id
    colleita.data = datos.data
    colleita.cantidade = datos.cantidade
    colleita.unidade = datos.unidade
    colleita.lote = datos.lote.strip()
    colleita.superficie_ha = datos.superficie_ha
    colleita.data_fin = datos.data_fin or datos.data
    colleita.albaran_factura = datos.albaran_factura or None
    colleita.obten_sementes = datos.obten_sementes
    colleita.obten_plantas = datos.obten_plantas
    colleita.sen_colleita_ambiental = datos.sen_colleita_ambiental
    colleita.restos_no_solo = datos.restos_no_solo
    colleita.maquina_id = datos.maquina_id
    colleita.num_repeticions = datos.num_repeticions
    colleita.duracion_h_ha = datos.duracion_h_ha
    colleita.destino_colleita = datos.destino_colleita or None
    colleita.destino_restos = datos.destino_restos or None
    colleita.notas = datos.notas or None


def crear_colleita(
    session: Session, actor: Usuario, datos: DatosColleita, hoxe: date | None = None
) -> Colleita:
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    if datos.superficie_ha is None:
        datos.superficie_ha = cultivo.superficie_ha
    colleita = Colleita(creado_por=actor.id)
    _copiar(colleita, datos)
    session.add(colleita)
    session.commit()
    return colleita


def actualizar_colleita(
    session: Session,
    actor: Usuario,
    colleita: Colleita,
    datos: DatosColleita,
    hoxe: date | None = None,
) -> Colleita:
    if colleita.baixa:
        raise OperacionNonPermitidaError("Unha colleita dada de baixa non se pode modificar")
    _, horta_actual = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_actual, actor, _ROLES_ESCRITURA)
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    if horta_id != horta_actual:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, horta_id, hoxe or date.today(), excepto_id=colleita.id)
    _copiar(colleita, datos)
    session.commit()
    return colleita


def dar_de_baixa_colleita(session: Session, actor: Usuario, colleita: Colleita) -> None:
    _, horta_id = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    colleita.baixa = True
    session.commit()


def listar_colleitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    cultivo_id: int | None = None,
    incluir_baixas: bool = False,
) -> list[Colleita]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = (
        session.query(Colleita)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if cultivo_id is not None:
        consulta = consulta.filter(Colleita.cultivo_id == cultivo_id)
    if not incluir_baixas:
        consulta = consulta.filter(Colleita.baixa.is_(False))
    return list(consulta.order_by(Colleita.data.desc(), Colleita.id.desc()))


def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
    """Primeiro lote libre do tipo AAAA-CULTIVO-NNN (p.ex. 2026-PATACA-001)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    nome = str(cultivo.cultivo_siex_codigo or cultivo.especie).upper().replace(" ", "-")
    existentes = _lotes_da_horta(session, horta_id)
    numero = 1
    while f"{data.year}-{nome}-{numero:03d}" in existentes:
        numero += 1
    return f"{data.year}-{nome}-{numero:03d}"


def rendemento_kg_ha(session: Session, actor: Usuario, cultivo_id: int) -> float | None:
    """kg por hectárea; None se falta a superficie ou hai colleitas noutras unidades."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    colleitas = listar_colleitas(session, actor, horta_id, cultivo_id=cultivo_id)
    if not cultivo.superficie_ha or not colleitas:
        return None
    if any(c.unidade not in _A_KG for c in colleitas):
        return None
    total = sum(c.cantidade * _A_KG[c.unidade] for c in colleitas)
    return round(total / cultivo.superficie_ha, 1)
```

### Paso 2 — crear o ficheiro `tests/services/test_colleitas.py`

Contido completo:

```python
from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import (
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    dar_de_baixa_colleita,
    listar_colleitas,
    propor_lote,
    rendemento_kg_ha,
)
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 23)


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def _escenario(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.5, data_inicio=date(2026, 3, 1))
    return ana, horta, cultivo


def _datos(cultivo, **cambios) -> DatosColleita:
    base = {"cultivo_id": cultivo.id, "data": date(2026, 7, 15), "cantidade": 1000.0,
            "unidade": "kg", "lote": "2026-PATACA-001"}
    return DatosColleita(**{**base, **cambios})


def test_crear_e_listar(session):
    ana, horta, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert colleita.creado_por == ana.id
    assert [c.lote for c in listar_colleitas(session, ana, horta.id)] == ["2026-PATACA-001"]


@pytest.mark.parametrize(
    ("cambios", "mensaxe"),
    [
        ({"cantidade": 0}, "maior que 0"),
        ({"unidade": "sacos"}, "Unidade non válida"),
        ({"data": date(2026, 12, 1)}, "futura"),
        ({"data": date(2026, 2, 1)}, "anterior ao inicio"),
        ({"superficie_ha": 0.9}, "maior ca do cultivo"),
        ({"lote": "  "}, "lote é obrigatorio"),
    ],
)
def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_colleita(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_lote_repetido_rexeitase(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xa existe"):
        crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)


def test_lector_non_pode_crear(session):
    ana, horta, cultivo = _escenario(session)
    bea = _crear_usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_colleita(session, bea, _datos(cultivo), hoxe=HOXE)


def test_propor_lote_salta_os_usados(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert propor_lote(session, ana, cultivo.id, date(2026, 8, 1)) == "2026-PATACA-002"


def test_baixa_non_se_lista_nin_se_modifica(session):
    ana, horta, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    dar_de_baixa_colleita(session, ana, colleita)
    assert listar_colleitas(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="dada de baixa"):
        actualizar_colleita(session, ana, colleita, _datos(cultivo, cantidade=5.0), hoxe=HOXE)


def test_actualizar_mantendo_o_mesmo_lote(session):
    ana, _, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_colleita(session, ana, colleita, _datos(cultivo, cantidade=900.0), hoxe=HOXE)
    assert colleita.cantidade == 900.0


def test_rendemento_en_kg_por_hectarea(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    crear_colleita(session, ana, _datos(cultivo, cantidade=1.0, unidade="t",
                                        lote="2026-PATACA-002"), hoxe=HOXE)
    assert rendemento_kg_ha(session, ana, cultivo.id) == 4000.0


def test_superficie_por_defecto_e_data_fin(session):
    ana, _, cultivo = _escenario(session)
    colleita = crear_colleita(session, ana, _datos(cultivo), hoxe=HOXE)
    assert colleita.superficie_ha == 0.5
    assert colleita.data_fin == colleita.data


def test_finalidade_so_para_procesado_ou_vino(session):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="viño ou a procesado"):
        crear_colleita(session, ana, _datos(cultivo, destino_colleita="6"), hoxe=HOXE)


def test_rendemento_sen_superficie_ou_con_unidades_non_kg(session):
    ana, _, cultivo = _escenario(session)
    crear_colleita(session, ana, _datos(cultivo, unidade="mazos"), hoxe=HOXE)
    assert rendemento_kg_ha(session, ana, cultivo.id) is None
```

### Paso 3 — `src/horta/services/cultivos.py`: campos editables novos

Antes:
```python
        "variedade_local_id",
```

Despois:
```python
        "variedade_local_id",
        "superficie_ha",
        "tipo_inicio",
        "data_inicio",
        "data_fin",
        "causa_baixa",
        "sistema_cultivo",
        "sistema_explotacion",
        "destino",
        "actividade_agraria",
        "certificacion_ecoloxica",
        "data_inicio_conversion",
        "producion_integrada",
        "procedencia_material",
        "provedor_material",
        "lote_material",
        "pasaporte_fitosanitario",
        "ropveg",
        "num_arbores",
        "marco_plantacion",
        "ano_plantacion",
        "unidades_produtivas",
        "ciclos_ano",
        "duracion_ciclo_dias",
        "cultivo_anterior_codigo",
        "obxectivo_colleita_kg_ha",
        "tipo_mvr",
        "detalle_mvr",
        "empresa_semente",
        "sementeira_directa",
        "tipo_cobertura_solo",
        "num_castineiros",
        "num_abeleiras",
        "num_nogueiras",
        "num_amendoeiras",
        "num_outros_froitos_casca",
        "data_fin_sementeira",
        "cantidade_semente_kg",
        "dose_sementeira_kg_ha",
        "densidade_plantas_ha",
        "material_tratado",
        "material_adquirido",
        "data_adquisicion_material",
```

### Paso 4 — mesmo ficheiro: importar Colleita

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

### Paso 5 — mesmo ficheiro: non borrar cultivos con colleitas

Antes:
```python
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
```

Despois:
```python
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten colleitas rexistradas e debe conservarse. "
            "Podes marcalo como rematado."
        )
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
```

## Criterios de aceptación

- Os tests de `tests/services/test_colleitas.py` pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
