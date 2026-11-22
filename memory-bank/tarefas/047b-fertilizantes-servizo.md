# Tarefa 047b — Servizo dos abonos e cálculo de nutrientes

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 047. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os meus abonos: crear (con validacións do CUE: provedor nos estercos e residuos, só un identificador do provedor), listar, encher dende o catálogo oficial (`datos_desde_siex`) e calcular os kg/ha de N, P₂O₅ e K₂O dunha dose (os líquidos só coa densidade). Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §1–2.

## Ficheiros a tocar

- `src/horta/services/fertilizantes.py` (**ficheiro novo**)
- `tests/services/test_fertilizantes.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/fertilizantes.py`

Contido completo:
```python
"""Os meus abonos: cada explotación garda os seus abonos unha vez e escólleos ao abonar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Fertilizante
from horta.models.fertilizante import FertilizanteSiex
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo MAT_FERTI: estercos (o 9 son inhibidores) e residuos, que piden provedor (CUE 9)
ESTERCOS = {"1", "2", "3", "4", "5", "6", "7", "8", "10"}
RESIDUOS = {"18", "19", "20", "21", "22", "23"}
# Unidades de dose (catálogo UNIDADES_MEDIDA) -> kg/ha; os líquidos precisan a densidade
_MASA_A_KG_HA = {"17": 1.0, "29": 1000.0, "49": 0.001, "60": 10000.0, "80": 10.0}
_VOLUME_A_L_HA = {"18": 1.0, "19": 1000.0, "59": 10000.0}
UNIDADES_DOSE = (*_MASA_A_KG_HA, *_VOLUME_A_L_HA)


@dataclass
class DatosFertilizante:
    nome: str
    material: str
    fertilizante_siex_codigo: int | None = None
    n_pct: float | None = None
    p2o5_pct: float | None = None
    k2o_pct: float | None = None
    liquido: bool = False
    densidade: float | None = None
    tratamento_estercos: str | None = None
    provedor_nome: str | None = None
    provedor_nif: str | None = None
    provedor_rega: str | None = None
    provedor_nima: str | None = None


def _validar(session: Session, datos: DatosFertilizante) -> None:
    hoxe = date.today()
    if not datos.nome.strip():
        raise OperacionNonPermitidaError("Pon un nome ao abono")
    validar_codigo(session, "material_fertilizante", datos.material, hoxe)
    for riqueza in (datos.n_pct, datos.p2o5_pct, datos.k2o_pct):
        if riqueza is not None and not 0 <= riqueza <= 100:
            raise OperacionNonPermitidaError("A riqueza ten que estar entre 0 e 100 %")
    if datos.densidade is not None and datos.densidade <= 0:
        raise OperacionNonPermitidaError("A densidade ten que ser maior que 0")
    identificadores = [x for x in (datos.provedor_nif, datos.provedor_rega, datos.provedor_nima)
                       if x]
    if len(identificadores) > 1:
        raise OperacionNonPermitidaError("Do provedor indica só un: NIF, REGA ou NIMA")
    if datos.material in ESTERCOS | RESIDUOS and not (datos.provedor_nome or "").strip():
        raise OperacionNonPermitidaError("Nos estercos e residuos indica de onde veñen")
    if datos.tratamento_estercos:
        if datos.material not in ESTERCOS:
            raise OperacionNonPermitidaError("O tratamento só se indica nos estercos")
        validar_codigo(session, "tratamento_estercos", datos.tratamento_estercos, hoxe)


def crear_fertilizante(
    session: Session, actor: Usuario, horta_id: int, datos: DatosFertilizante
) -> Fertilizante:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos)
    nome = datos.nome.strip()
    if session.query(Fertilizante).filter_by(horta_id=horta_id, nome=nome).first():
        raise OperacionNonPermitidaError(f"Xa tes un abono chamado {nome}")
    fertilizante = Fertilizante(horta_id=horta_id, **{**vars(datos), "nome": nome})
    session.add(fertilizante)
    session.commit()
    return fertilizante


def listar_fertilizantes(
    session: Session, actor: Usuario, horta_id: int, incluir_inactivos: bool = False
) -> list[Fertilizante]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Fertilizante).filter_by(horta_id=horta_id)
    if not incluir_inactivos:
        consulta = consulta.filter(Fertilizante.activo.is_(True))
    return list(consulta.order_by(Fertilizante.nome))


def datos_desde_siex(session: Session, codigo: int) -> DatosFertilizante:
    """Enche un abono novo cos datos do catálogo oficial (nome, material e riqueza)."""
    oficial = session.get(FertilizanteSiex, codigo)
    if oficial is None or oficial.data_baixa is not None:
        raise OperacionNonPermitidaError("Ese produto non está no catálogo oficial")
    return DatosFertilizante(
        nome=oficial.nome, material=oficial.material, fertilizante_siex_codigo=codigo,
        n_pct=oficial.n_pct, p2o5_pct=oficial.p2o5_pct, k2o_pct=oficial.k2o_pct,
        liquido=oficial.liquido, densidade=oficial.densidade,
    )


def dose_kg_ha(dose: float, unidade: str, densidade: float | None) -> float | None:
    """Dose en kg/ha; None se é un líquido sen densidade coñecida ou a unidade non é de dose."""
    if unidade in _MASA_A_KG_HA:
        return dose * _MASA_A_KG_HA[unidade]
    if unidade in _VOLUME_A_L_HA and densidade:
        return dose * _VOLUME_A_L_HA[unidade] * densidade
    return None


def nutrientes_kg_ha(
    fertilizante: Fertilizante, dose: float, unidade: str
) -> tuple[float, float, float] | None:
    """kg/ha de N, P₂O₅ e K₂O que leva unha dose; None se non se pode calcular."""
    kg_ha = dose_kg_ha(dose, unidade, fertilizante.densidade)
    if kg_ha is None:
        return None
    n, p, k = (fertilizante.n_pct or 0, fertilizante.p2o5_pct or 0, fertilizante.k2o_pct or 0)
    return round(kg_ha * n / 100, 1), round(kg_ha * p / 100, 1), round(kg_ha * k / 100, 1)
```

### Paso 2 — crear o ficheiro `tests/services/test_fertilizantes.py`

Contido completo:
```python
import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import (
    DatosFertilizante,
    crear_fertilizante,
    datos_desde_siex,
    dose_kg_ha,
    listar_fertilizantes,
    nutrientes_kg_ha,
)
from horta.services.hortas import crear_horta


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for codigo in ("5", "14"):
        session.add(CatalogoValor(catalogo="material_fertilizante", codigo=codigo,
                                  descricion="m", version_id=v.id))
    session.add(FertilizanteSiex(codigo=2, material="14", nome="NITRATO (34,5-00-00)",
                                 n_pct=34.5, version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_crear_desde_o_catalogo_oficial(session):
    ana, horta = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, datos_desde_siex(session, 2))
    assert abono.material == "14" and abono.n_pct == 34.5
    assert [f.nome for f in listar_fertilizantes(session, ana, horta.id)] == [
        "NITRATO (34,5-00-00)"]


def test_esterco_pide_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="de onde veñen"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="Esterco", material="5"))
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="5", provedor_nome="Casa", n_pct=0.6))
    assert abono.provedor_nome == "Casa"


def test_so_un_identificador_do_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="só un"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="E", material="5", provedor_nome="X", provedor_nif="1", provedor_rega="2"))


def test_nome_repetido(session):
    ana, horta = _escenario(session)
    crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="Nitrato", material="14"))
    with pytest.raises(OperacionNonPermitidaError, match="Xa tes"):
        crear_fertilizante(session, ana, horta.id,
                           DatosFertilizante(nome=" Nitrato ", material="14"))


@pytest.mark.parametrize(("dose", "unidade", "densidade", "esperado"), [
    (200, "17", None, 200),      # kg/ha
    (2, "29", None, 2000),       # t/ha
    (50, "80", None, 500),       # g/m²
    (100, "18", 1.4, 140),       # L/ha con densidade
    (100, "18", None, None),     # L/ha sen densidade: non se sabe
    (3, "2", None, None),        # ha non é unha dose
])
def test_dose_kg_ha(dose, unidade, densidade, esperado):
    assert dose_kg_ha(dose, unidade, densidade) == esperado


def test_nutrientes_dunha_dose(session):
    ana, horta = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK", material="14", n_pct=15, p2o5_pct=15, k2o_pct=15))
    assert nutrientes_kg_ha(abono, 200, "17") == (30.0, 30.0, 30.0)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense crear abonos e calcular os nutrientes dunha dose.
