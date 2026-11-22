# Tarefa 053b — Servizo das análises

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 053. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear, editar, dar de baixa e listar análises. Valida a data, os catálogos, que parcela, cultivo e lote sexan da explotación e os parámetros do solo (só en análises de solo; porcentaxes 0–100, pH 0–14). Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §5. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/services/analises.py` (**ficheiro novo**)
- `tests/services/test_analises.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/analises.py`

Contido completo:
```python
"""Análises de cultivo, produto colleitado, solo ou auga (CUE bloque 13). Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.analise import Analise, AnaliseSubstancia, AnaliseTipo
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
SOLO = "3"  # catálogo MATERIAL_ANALIZADO
_PORCENTAXES = ("materia_organica", "area", "limo", "arxila", "n_total")
CAMPOS_SOLO = (*_PORCENTAXES, "ph", "fosforo_ppm", "potasio_ppm", "conductividade")


@dataclass
class DatosAnalise:
    material_analizado: str
    data_mostraxe: date
    tipos: list[str] = field(default_factory=list)
    substancias: list[str] = field(default_factory=list)
    laboratorio: str | None = None
    laboratorio_nif: str | None = None
    num_boletin: str | None = None
    parcela_id: int | None = None
    cultivo_id: int | None = None
    colleita_id: int | None = None
    solo: dict[str, float | None] = field(default_factory=dict)
    notas: str | None = None


def _horta_de(session: Session, modelo: type, ident: int | None) -> int | None:
    if ident is None:
        return None
    obxecto = session.get(modelo, ident)
    if obxecto is None:
        return -1
    if isinstance(obxecto, Parcela):
        return obxecto.horta_id
    cultivo = obxecto if isinstance(obxecto, Cultivo) else session.get(Cultivo, obxecto.cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    return parcela.horta_id if parcela else -1


def _validar(session: Session, horta_id: int, datos: DatosAnalise, hoxe: date) -> None:
    if datos.data_mostraxe > hoxe:
        raise OperacionNonPermitidaError("A data da mostra non pode ser futura")
    validar_codigo(session, "material_analizado", datos.material_analizado, datos.data_mostraxe)
    for codigo in datos.tipos:
        validar_codigo(session, "tipo_analise", codigo, datos.data_mostraxe)
    for codigo in datos.substancias:
        validar_codigo(session, "substancia_activa", codigo, datos.data_mostraxe)
    for modelo, ident in ((Parcela, datos.parcela_id), (Cultivo, datos.cultivo_id),
                          (Colleita, datos.colleita_id)):
        if _horta_de(session, modelo, ident) not in (None, horta_id):
            raise OperacionNonPermitidaError("A parcela, cultivo ou lote non é desta explotación")
    valores = {k: v for k, v in datos.solo.items() if v is not None}
    if valores and datos.material_analizado != SOLO:
        raise OperacionNonPermitidaError("Os parámetros do solo só van nas análises de solo")
    if set(valores) - set(CAMPOS_SOLO):
        raise OperacionNonPermitidaError("Parámetro do solo descoñecido")
    for campo in _PORCENTAXES:
        if campo in valores and not 0 <= valores[campo] <= 100:
            raise OperacionNonPermitidaError("As porcentaxes van de 0 a 100")
    if "ph" in valores and not 0 <= valores["ph"] <= 14:
        raise OperacionNonPermitidaError("O pH vai de 0 a 14")


def _copiar(analise: Analise, horta_id: int, datos: DatosAnalise) -> None:
    analise.horta_id = horta_id
    analise.material_analizado = datos.material_analizado
    analise.data_mostraxe = datos.data_mostraxe
    analise.laboratorio = datos.laboratorio or None
    analise.laboratorio_nif = datos.laboratorio_nif or None
    analise.num_boletin = datos.num_boletin or None
    analise.parcela_id = datos.parcela_id
    analise.cultivo_id = datos.cultivo_id
    analise.colleita_id = datos.colleita_id
    for campo in CAMPOS_SOLO:
        setattr(analise, campo, datos.solo.get(campo))
    analise.notas = datos.notas or None
    analise.tipos = [AnaliseTipo(codigo=c) for c in datos.tipos]
    analise.substancias = [AnaliseSubstancia(codigo=c) for c in datos.substancias]


def crear_analise(
    session: Session, actor: Usuario, horta_id: int, datos: DatosAnalise,
    hoxe: date | None = None,
) -> Analise:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, horta_id, datos, hoxe or date.today())
    analise = Analise(creado_por=actor.id)
    _copiar(analise, horta_id, datos)
    session.add(analise)
    session.commit()
    return analise


def actualizar_analise(
    session: Session, actor: Usuario, analise: Analise, datos: DatosAnalise,
    hoxe: date | None = None,
) -> Analise:
    if analise.baixa:
        raise OperacionNonPermitidaError("Unha análise dada de baixa non se pode modificar")
    comprobar_rol_horta(session, analise.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, analise.horta_id, datos, hoxe or date.today())
    _copiar(analise, analise.horta_id, datos)
    session.commit()
    return analise


def dar_de_baixa_analise(session: Session, actor: Usuario, analise: Analise) -> None:
    comprobar_rol_horta(session, analise.horta_id, actor, _ROLES_ESCRITURA)
    analise.baixa = True
    session.commit()


def listar_analises(session: Session, actor: Usuario, horta_id: int) -> list[Analise]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Analise).filter_by(horta_id=horta_id, baixa=False)
                .order_by(Analise.data_mostraxe.desc(), Analise.id.desc()))
```

### Paso 2 — crear o ficheiro `tests/services/test_analises.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.analises import (
    DatosAnalise,
    actualizar_analise,
    crear_analise,
    dar_de_baixa_analise,
    listar_analises,
)
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela

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
    for catalogo, codigo in [("material_analizado", "2"), ("material_analizado", "3"),
                             ("tipo_analise", "1"), ("tipo_analise", "5"),
                             ("substancia_activa", "2")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    return ana, horta, parcela, cultivo


def test_analise_de_solo_dunha_parcela(session):
    ana, horta, parcela, _ = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(
        material_analizado="3", data_mostraxe=date(2026, 3, 1), tipos=["5"],
        parcela_id=parcela.id, laboratorio="Lab", solo={"ph": 5.8, "materia_organica": 4.2}),
        hoxe=HOXE)
    assert analise.ph == 5.8 and analise.materia_organica == 4.2
    assert [t.codigo for t in analise.tipos] == ["5"]
    assert listar_analises(session, ana, horta.id) == [analise]


def test_residuos_no_produto(session):
    ana, horta, _, cultivo = _escenario(session)
    analise = crear_analise(session, ana, horta.id, DatosAnalise(
        material_analizado="2", data_mostraxe=date(2026, 8, 1), tipos=["1"],
        substancias=["2"], cultivo_id=cultivo.id), hoxe=HOXE)
    assert [s.codigo for s in analise.substancias] == ["2"]


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"data_mostraxe": date(2026, 11, 1)}, "futura"),
    ({"material_analizado": "2", "solo": {"ph": 6}}, "só van nas análises de solo"),
    ({"solo": {"ph": 15}}, "pH"),
    ({"solo": {"arxila": 120}}, "porcentaxes"),
    ({"tipos": ["9"]}, "non existe"),
])
def test_validacions(session, cambios, mensaxe):
    ana, horta, _, _ = _escenario(session)
    datos = {"material_analizado": "3", "data_mostraxe": date(2026, 3, 1), **cambios}
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_analise(session, ana, horta.id, DatosAnalise(**datos), hoxe=HOXE)


def test_cultivo_doutra_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    outro = crear_cultivo(session, ana, crear_parcela(session, ana, outra.id, "P").id, "X")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=date(2026, 3, 1), cultivo_id=outro.id),
            hoxe=HOXE)


def test_lector_non_pode_e_baixa(session):
    ana, horta, _, _ = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    datos = DatosAnalise(material_analizado="3", data_mostraxe=date(2026, 3, 1))
    with pytest.raises(PermisoDenegadoError):
        crear_analise(session, bea, horta.id, datos, hoxe=HOXE)
    analise = crear_analise(session, ana, horta.id, datos, hoxe=HOXE)
    actualizar_analise(session, ana, analise, DatosAnalise(
        material_analizado="3", data_mostraxe=date(2026, 3, 2)), hoxe=HOXE)
    dar_de_baixa_analise(session, ana, analise)
    assert listar_analises(session, ana, horta.id) == []
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense apuntar análises por servizo, con probas.
