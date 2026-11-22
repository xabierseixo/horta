# Tarefa 063b — Servizo dos tratamentos de instalacións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 063. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Crear, editar, dar de baixa e listar, con validacións (tipo, data, que se tratou, produto, cantidades e catálogos). Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/tratamentos_instalacion.py` (**ficheiro novo**)
- `tests/services/test_tratamentos_instalacion.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/tratamentos_instalacion.py`

Contido completo:
```python
"""Tratamentos de postcolleita, locais de almacenamento e transporte (caderno 3.3–3.5)."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import date

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.models.tratamento_instalacion import TIPOS_INSTALACION, TratamentoInstalacion
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass
class DatosTratamentoInstalacion:
    tipo: str
    data: date
    obxecto: str
    referencia_catastral: str | None = None
    problema_tipo: str | None = None
    problema_codigo: str | None = None
    xustificacion: str | None = None
    cantidade_tratada: float | None = None
    tipo_produto: str | None = None
    nome_comercial: str | None = None
    num_rexistro: str | None = None
    materia_activa: str | None = None
    cantidade_utilizada: float | None = None
    unidade: str | None = None
    notas: str | None = None


def _validar(session: Session, datos: DatosTratamentoInstalacion, hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
    if not datos.obxecto.strip():
        raise OperacionNonPermitidaError("Indica que se tratou")
    if not (datos.nome_comercial or datos.materia_activa):
        raise OperacionNonPermitidaError("Indica o produto (nome comercial ou materia activa)")
    for cantidade in (datos.cantidade_tratada, datos.cantidade_utilizada):
        if cantidade is not None and cantidade <= 0:
            raise OperacionNonPermitidaError("As cantidades teñen que ser maiores que 0")
    if datos.problema_codigo:
        if datos.problema_tipo not in TIPOS_PROBLEMA:
            raise OperacionNonPermitidaError("Tipo de problema descoñecido")
        validar_codigo(session, datos.problema_tipo, datos.problema_codigo, datos.data)
    for catalogo, codigo in (("xustificacion", datos.xustificacion),
                             ("tipo_produto", datos.tipo_produto),
                             ("unidade_medida", datos.unidade)):
        if codigo:
            validar_codigo(session, catalogo, codigo, datos.data)


def _copiar(tratamento: TratamentoInstalacion, datos: DatosTratamentoInstalacion) -> None:
    for campo in fields(datos):
        valor = getattr(datos, campo.name)
        setattr(tratamento, campo.name, valor.strip() or None if isinstance(valor, str)
                and campo.name not in ("tipo", "obxecto") else valor)
    tratamento.obxecto = datos.obxecto.strip()


def crear_tratamento_instalacion(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamentoInstalacion,
    hoxe: date | None = None,
) -> TratamentoInstalacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    tratamento = TratamentoInstalacion(horta_id=horta_id, creado_por=actor.id)
    _copiar(tratamento, datos)
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento_instalacion(
    session: Session, actor: Usuario, tratamento: TratamentoInstalacion,
    datos: DatosTratamentoInstalacion, hoxe: date | None = None,
) -> TratamentoInstalacion:
    if tratamento.baixa:
        raise OperacionNonPermitidaError("Un tratamento dado de baixa non se pode modificar")
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    _copiar(tratamento, datos)
    session.commit()
    return tratamento


def dar_de_baixa_tratamento_instalacion(
    session: Session, actor: Usuario, tratamento: TratamentoInstalacion
) -> None:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos_instalacion(
    session: Session, actor: Usuario, horta_id: int
) -> list[TratamentoInstalacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(TratamentoInstalacion).filter_by(horta_id=horta_id, baixa=False)
                .order_by(TratamentoInstalacion.data.desc(), TratamentoInstalacion.id.desc()))
```

### Paso 2 — crear o ficheiro `tests/services/test_tratamentos_instalacion.py`

Contido completo:
```python
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    actualizar_tratamento_instalacion,
    crear_tratamento_instalacion,
    dar_de_baixa_tratamento_instalacion,
    listar_tratamentos_instalacion,
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
    for catalogo, codigo in [("praga", "7"), ("unidade_medida", "4")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    session.commit()
    ana = _usuario(session, "ana@example.com")
    return ana, crear_horta(session, ana, "Horta")


def _datos(**cambios):
    base = {"tipo": "local", "data": date(2026, 6, 1), "obxecto": "Alpendre das patacas",
            "problema_tipo": "praga", "problema_codigo": "7", "cantidade_tratada": 30,
            "nome_comercial": "Produto X", "cantidade_utilizada": 0.5, "unidade": "4"}
    base.update(cambios)
    return DatosTratamentoInstalacion(**base)


def test_crear_editar_e_dar_de_baixa(session):
    ana, horta = _escenario(session)
    t = crear_tratamento_instalacion(session, ana, horta.id, _datos(), hoxe=HOXE)
    assert t.creado_por == ana.id and t.referencia_catastral is None
    actualizar_tratamento_instalacion(session, ana, t, _datos(cantidade_tratada=40), hoxe=HOXE)
    assert t.cantidade_tratada == 40
    assert listar_tratamentos_instalacion(session, ana, horta.id) == [t]
    dar_de_baixa_tratamento_instalacion(session, ana, t)
    assert listar_tratamentos_instalacion(session, ana, horta.id) == []


@pytest.mark.parametrize(("cambios", "mensaxe"), [
    ({"tipo": "almacen"}, "postcolleita"),
    ({"data": date(2026, 11, 1)}, "futura"),
    ({"obxecto": " "}, "que se tratou"),
    ({"nome_comercial": None}, "produto"),
    ({"cantidade_utilizada": 0}, "maiores que 0"),
    ({"problema_codigo": "99"}, "non existe"),
])
def test_validacions(session, cambios, mensaxe):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_tratamento_instalacion(session, ana, horta.id, _datos(**cambios), hoxe=HOXE)


def test_lector_non_pode(session):
    ana, horta = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_tratamento_instalacion(session, bea, horta.id, _datos(), hoxe=HOXE)

```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pódense apuntar estes tratamentos por servizo, con probas.
