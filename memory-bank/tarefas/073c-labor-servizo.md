# Tarefa 073c — Labores culturais: servizo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 073b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear, editar, dar de baixa e listar labores, con validacións (datas, superficie, catálogos, máquina e persoa da explotación) e os restos só nos labores que os pregunta o CUE. Deseño: `docs/superpowers/specs/2026-10-25-labores-culturais-design.md`

## Ficheiros a tocar

- `src/horta/services/labores.py` (**ficheiro novo**)
- `tests/services/test_labores.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/labores.py`

Contido completo:
```python
"""Labores culturais dos cultivos (CUE bloque 5). Un cultivo por labor. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo TIPO_LABOR: onde o CUE pregunta se os restos quedaron no chan
DESBROCE = "5"
PODAS = ("7", "11", "12")


@dataclass
class DatosLabor:
    cultivo_id: int
    data_inicio: date
    tipo_labor: str
    data_fin: date | None = None
    superficie_ha: float | None = None
    restos_desbroce_no_solo: bool = False
    restos_poda_no_solo: bool = False
    tipo_cobertura: str | None = None
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h: float | None = None
    persoa_id: int | None = None
    notas: str | None = None


def _cultivo_e_parcela(session: Session, cultivo_id: int) -> tuple[Cultivo, Parcela]:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    return cultivo, parcela


def _validar(session: Session, datos: DatosLabor, cultivo: Cultivo, horta_id: int,
             hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie do labor é maior ca do cultivo")
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
    for valor, texto in ((datos.num_repeticions, "repeticións"), (datos.duracion_h, "horas")):
        if valor is not None and valor <= 0:
            raise OperacionNonPermitidaError(f"O número de {texto} ten que ser maior que 0")
    validar_codigo(session, "tipo_labor", datos.tipo_labor, datos.data_inicio)
    if datos.tipo_cobertura:
        validar_codigo(session, "tipo_cobertura_solo", datos.tipo_cobertura, datos.data_inicio)
    if datos.maquina_id is not None:
        maquina = session.get(Maquina, datos.maquina_id)
        if maquina is None or maquina.horta_id != horta_id:
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
    if datos.persoa_id is not None:
        persoa = session.get(Persoa, datos.persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")


def _copiar(labor: Labor, datos: DatosLabor, cultivo: Cultivo, parcela: Parcela) -> None:
    labor.horta_id = parcela.horta_id
    labor.cultivo_id = datos.cultivo_id
    labor.data_inicio = datos.data_inicio
    labor.data_fin = datos.data_fin or datos.data_inicio
    labor.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
    labor.tipo_labor = datos.tipo_labor
    # Os restos só se anotan nos labores onde o CUE os pregunta
    labor.restos_desbroce_no_solo = datos.tipo_labor == DESBROCE and datos.restos_desbroce_no_solo
    labor.restos_poda_no_solo = datos.tipo_labor in PODAS and datos.restos_poda_no_solo
    labor.tipo_cobertura = datos.tipo_cobertura or cultivo.tipo_cobertura_solo
    labor.maquina_id = datos.maquina_id
    labor.num_repeticions = datos.num_repeticions
    labor.duracion_h = datos.duracion_h
    labor.persoa_id = datos.persoa_id
    labor.notas = datos.notas or None


def crear_labor(
    session: Session, actor: Usuario, datos: DatosLabor, hoxe: date | None = None
) -> Labor:
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, parcela.horta_id, hoxe or date.today())
    labor = Labor(creado_por=actor.id)
    _copiar(labor, datos, cultivo, parcela)
    session.add(labor)
    session.commit()
    return labor


def actualizar_labor(
    session: Session, actor: Usuario, labor: Labor, datos: DatosLabor, hoxe: date | None = None
) -> Labor:
    if labor.baixa:
        raise OperacionNonPermitidaError("Un labor dado de baixa non se pode modificar")
    comprobar_rol_horta(session, labor.horta_id, actor, _ROLES_ESCRITURA)
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    if parcela.horta_id != labor.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, labor.horta_id, hoxe or date.today())
    _copiar(labor, datos, cultivo, parcela)
    session.commit()
    return labor


def dar_de_baixa_labor(session: Session, actor: Usuario, labor: Labor) -> None:
    comprobar_rol_horta(session, labor.horta_id, actor, _ROLES_ESCRITURA)
    labor.baixa = True
    session.commit()


def listar_labores(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Labor]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Labor).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Labor.data_inicio.desc(), Labor.id.desc()))


def ultimo_labor(session: Session, cultivo_id: int) -> str | None:
    """O tipo do último labor dese cultivo, para propoñelo no seguinte."""
    labor = (session.query(Labor).filter_by(cultivo_id=cultivo_id, baixa=False)
             .order_by(Labor.data_inicio.desc(), Labor.id.desc()).first())
    return labor.tipo_labor if labor else None
```

### Paso 2 — crear o ficheiro `tests/services/test_labores.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.labores import (
    DatosLabor,
    actualizar_labor,
    crear_labor,
    dar_de_baixa_labor,
    listar_labores,
    ultimo_labor,
)
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela, eliminar_parcela

HOXE = date(2026, 10, 25)


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("tipo_labor", "1"), ("tipo_labor", "5"), ("tipo_labor", "7"),
                             ("tipo_cobertura_solo", "1"), ("tipo_cobertura_solo", "3")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    cultivo = crear_cultivo(session, ana, parcela.id, "Maceira")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.2, tipo_cobertura_solo="3")
    return ana, horta, parcela, cultivo


def _datos(cultivo, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 3, 1), "tipo_labor": "7"}
    base.update(cambios)
    return DatosLabor(**base)


def test_crear_labor_cos_valores_por_defecto(session):
    ana, horta, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo, restos_poda_no_solo=True), hoxe=HOXE)
    assert labor.data_fin == labor.data_inicio
    assert labor.superficie_ha == 0.2
    assert labor.tipo_cobertura == "3"  # a do cultivo
    assert labor.restos_poda_no_solo and not labor.restos_desbroce_no_solo
    assert labor.creado_por == ana.id
    assert listar_labores(session, ana, horta.id) == [labor]


def test_restos_so_nos_labores_que_os_preguntan(session):
    ana, _, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo, tipo_labor="1", restos_poda_no_solo=True,
                                             restos_desbroce_no_solo=True), hoxe=HOXE)
    assert not labor.restos_poda_no_solo and not labor.restos_desbroce_no_solo
    desbroce = crear_labor(session, ana, _datos(cultivo, tipo_labor="5",
                                                restos_desbroce_no_solo=True), hoxe=HOXE)
    assert desbroce.restos_desbroce_no_solo


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 2, 1)}, "anterior"),
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
    ({"superficie_ha": 0}, "maior que 0"),
    ({"num_repeticions": 0}, "repeticións"),
    ({"tipo_labor": "99"}, None),
    ({"tipo_cobertura": "99"}, None),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_labor(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_maquina_doutra_explotacion(session):
    ana, _, _, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    maquina = crear_maquina(session, ana, outra.id, "Tractor", id_equipo_non_inscribible="T1")
    with pytest.raises(OperacionNonPermitidaError, match="máquina"):
        crear_labor(session, ana, _datos(cultivo, maquina_id=maquina.id), hoxe=HOXE)


def test_editar_baixa_e_ultimo_labor(session):
    ana, horta, _, cultivo = _escenario(session)
    labor = crear_labor(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_labor(session, ana, labor, _datos(cultivo, tipo_labor="1", num_repeticions=2,
                                                 duracion_h=1.5), hoxe=HOXE)
    assert (labor.tipo_labor, labor.num_repeticions, labor.duracion_h) == ("1", 2, 1.5)
    assert ultimo_labor(session, cultivo.id) == "1"
    dar_de_baixa_labor(session, ana, labor)
    assert listar_labores(session, ana, horta.id) == []
    with pytest.raises(OperacionNonPermitidaError, match="baixa"):
        actualizar_labor(session, ana, labor, _datos(cultivo), hoxe=HOXE)


def test_lector_non_pode(session):
    ana, horta, _, cultivo = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_labor(session, bea, _datos(cultivo), hoxe=HOXE)


def test_cultivo_e_parcela_con_labores_conservanse(session):
    ana, _, parcela, cultivo = _escenario(session)
    crear_labor(session, ana, _datos(cultivo), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="labores"):
        eliminar_cultivo(session, ana, cultivo)
    with pytest.raises(OperacionNonPermitidaError, match="labores"):
        eliminar_parcela(session, ana, parcela)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existe services/labores.py coas súas probas.
