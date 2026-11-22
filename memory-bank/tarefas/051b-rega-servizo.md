# Tarefa 051b — Servizo da rega

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 051. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear, editar, dar de baixa e listar regas. A orixe da auga, se non se indica, é a da parcela; a superficie, a do cultivo. `ultimo_sistema_rega` propón o sistema da rega anterior e `litros_estimados` é a calculadora para quen non sabe os litros (minutos × l/min ou regadeiras × litros). Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §3. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/services/regas.py` (**ficheiro novo**)
- `tests/services/test_regas.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/regas.py`

Contido completo:
```python
"""Regas dos cultivos (CUE bloque 10). Un cultivo por rega. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.rega import Rega, RegaBoaPractica
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo UNIDADES_MEDIDA: m³ e litros
UNIDADES_AUGA = ("3", "4")


@dataclass
class DatosRega:
    cultivo_id: int
    data_inicio: date
    sistema_rega: str
    cantidade: float
    unidade: str = "4"
    data_fin: date | None = None
    superficie_ha: float | None = None
    orixe_auga: str | None = None
    tipo_enerxia: str | None = None
    num_contador: str | None = None
    boas_practicas: list[str] = field(default_factory=list)
    notas: str | None = None


def _cultivo_e_parcela(session: Session, cultivo_id: int) -> tuple[Cultivo, Parcela]:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    return cultivo, parcela


def _validar(session: Session, datos: DatosRega, cultivo: Cultivo, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie regada é maior ca do cultivo")
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade de auga ten que ser maior que 0")
    if datos.unidade not in UNIDADES_AUGA:
        raise OperacionNonPermitidaError("A auga vai en litros ou m³")
    validar_codigo(session, "sistema_rega", datos.sistema_rega, datos.data_inicio)
    if datos.orixe_auga:
        validar_codigo(session, "orixe_auga", datos.orixe_auga, datos.data_inicio)
    if datos.tipo_enerxia:
        validar_codigo(session, "tipo_enerxia", datos.tipo_enerxia, datos.data_inicio)
    for codigo in datos.boas_practicas:
        valor = validar_codigo(session, "boas_practicas", codigo, datos.data_inicio)
        if "rega" not in (valor.categoria or ""):
            raise OperacionNonPermitidaError(f"A boa práctica {codigo} non é de rega")


def _copiar(rega: Rega, datos: DatosRega, cultivo: Cultivo, parcela: Parcela) -> None:
    rega.horta_id = parcela.horta_id
    rega.cultivo_id = datos.cultivo_id
    rega.data_inicio = datos.data_inicio
    rega.data_fin = datos.data_fin or datos.data_inicio
    rega.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
    rega.sistema_rega = datos.sistema_rega
    rega.cantidade = datos.cantidade
    rega.unidade = datos.unidade
    rega.orixe_auga = datos.orixe_auga or parcela.orixe_auga
    rega.tipo_enerxia = datos.tipo_enerxia or None
    rega.num_contador = datos.num_contador or None
    rega.notas = datos.notas or None
    rega.boas_practicas = [RegaBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_rega(
    session: Session, actor: Usuario, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, hoxe or date.today())
    rega = Rega(creado_por=actor.id)
    _copiar(rega, datos, cultivo, parcela)
    session.add(rega)
    session.commit()
    return rega


def actualizar_rega(
    session: Session, actor: Usuario, rega: Rega, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    if rega.baixa:
        raise OperacionNonPermitidaError("Unha rega dada de baixa non se pode modificar")
    comprobar_rol_horta(session, rega.horta_id, actor, _ROLES_ESCRITURA)
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    if parcela.horta_id != rega.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, hoxe or date.today())
    _copiar(rega, datos, cultivo, parcela)
    session.commit()
    return rega


def dar_de_baixa_rega(session: Session, actor: Usuario, rega: Rega) -> None:
    comprobar_rol_horta(session, rega.horta_id, actor, _ROLES_ESCRITURA)
    rega.baixa = True
    session.commit()


def listar_regas(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Rega]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Rega).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Rega.data_inicio.desc(), Rega.id.desc()))


def ultimo_sistema_rega(session: Session, cultivo_id: int) -> str | None:
    """O sistema de rega da última rega dese cultivo, para propoñelo na seguinte."""
    rega = (session.query(Rega).filter_by(cultivo_id=cultivo_id, baixa=False)
            .order_by(Rega.data_inicio.desc(), Rega.id.desc()).first())
    return rega.sistema_rega if rega else None


def litros_estimados(
    minutos: float | None = None, litros_minuto: float | None = None,
    regadeiras: float | None = None, litros_regadeira: float | None = None,
) -> float | None:
    """Calculadora para quen non sabe os litros: minutos × l/min ou regadeiras × litros."""
    if minutos and litros_minuto:
        return round(minutos * litros_minuto, 1)
    if regadeiras and litros_regadeira:
        return round(regadeiras * litros_regadeira, 1)
    return None
```

### Paso 2 — crear o ficheiro `tests/services/test_regas.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import actualizar_parcela, crear_parcela
from horta.services.regas import (
    DatosRega,
    actualizar_rega,
    crear_rega,
    dar_de_baixa_rega,
    listar_regas,
    litros_estimados,
    ultimo_sistema_rega,
)

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
    for catalogo, codigo, categoria in [
        ("sistema_rega", "6", None), ("orixe_auga", "2", None), ("orixe_auga", "3", None),
        ("boas_practicas", "23", "rega"), ("boas_practicas", "50", "fito"),
    ]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  categoria=categoria, version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.5)
    actualizar_parcela(session, ana, parcela, orixe_auga="2")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    actualizar_cultivo(session, ana, cultivo, superficie_ha=0.01)
    return ana, horta, cultivo


def _datos(cultivo, **cambios):
    base = {"cultivo_id": cultivo.id, "data_inicio": date(2026, 7, 1), "sistema_rega": "6",
            "cantidade": 300}
    base.update(cambios)
    return DatosRega(**base)


def test_crear_rega_cos_valores_por_defecto(session):
    ana, horta, cultivo = _escenario(session)
    rega = crear_rega(session, ana, _datos(cultivo), hoxe=HOXE)
    assert rega.superficie_ha == 0.01 and rega.data_fin == date(2026, 7, 1)
    assert rega.unidade == "4" and rega.orixe_auga == "2"  # a orixe da parcela
    assert rega.creado_por == ana.id
    assert listar_regas(session, ana, horta.id) == [rega]
    assert ultimo_sistema_rega(session, cultivo.id) == "6"


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_inicio": date(2026, 11, 1)}, "futura"),
    ({"data_fin": date(2026, 6, 1)}, "anterior"),
    ({"superficie_ha": 0.02}, "maior ca do cultivo"),
    ({"cantidade": 0}, "maior que 0"),
    ({"unidade": "5"}, "litros ou m³"),
    ({"boas_practicas": ["50"]}, "non é de rega"),
])
def test_validacions(session, cambios, mensaxe):
    ana, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_rega(session, ana, _datos(cultivo, **cambios), hoxe=HOXE)


def test_lector_non_pode_regar(session):
    ana, horta, cultivo = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_rega(session, bea, _datos(cultivo), hoxe=HOXE)


def test_actualizar_e_dar_de_baixa(session):
    ana, horta, cultivo = _escenario(session)
    rega = crear_rega(session, ana, _datos(cultivo), hoxe=HOXE)
    actualizar_rega(session, ana, rega, _datos(cultivo, cantidade=2, unidade="3",
                                               orixe_auga="3", boas_practicas=["23"]),
                    hoxe=HOXE)
    assert rega.cantidade == 2 and rega.orixe_auga == "3"
    assert [b.codigo for b in rega.boas_practicas] == ["23"]
    dar_de_baixa_rega(session, ana, rega)
    assert listar_regas(session, ana, horta.id) == []


@pytest.mark.parametrize(("args", "esperado"), [
    ({"minutos": 20, "litros_minuto": 12}, 240),
    ({"regadeiras": 6, "litros_regadeira": 10}, 60),
    ({"minutos": 20}, None),
    ({}, None),
])
def test_litros_estimados(args, esperado):
    assert litros_estimados(**args) == esperado
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense apuntar regas por servizo, con probas.
