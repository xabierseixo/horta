# Cultivos, Tratamentos e Fertilización — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Engadir as entidades Cultivo, Tratamento e Fertilización (ligadas a Parcela/Cultivo), cos seus servizos, migración e pestanas de UI, seguindo exactamente o patrón xa establecido en Parcela/Animal.

**Architecture:** Cultivo liga a Parcela (FK), Tratamento e Fertilización ligan a Cultivo (FK). Sen `relationship()` de SQLAlchemy en ningures (decisión xa establecida no proxecto) — toda resolución de permisos e cascada faise con consultas/queries explícitas. Tratamento/Fertilización usan baixa lóxica (nunca `DELETE` físico) por esixencia de conservación normativa; Cultivo/Parcela/Horta seguen usando borrado físico con cascada manual.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0, Alembic, NiceGUI, pytest.

**Spec:** `docs/superpowers/specs/2026-09-25-cultivos-tratamentos-fertilizacion-design.md`

## Global Constraints

- Identificadores, mensaxes e textos da UI en galego.
- Sen `relationship()` de SQLAlchemy — toda relación resólvese con FK soltas e consultas/joins explícitos, coma xa fan Parcela/Animal/HortaMembro.
- Tratamento e Fertilización nunca se borran fisicamente por unha acción individual do usuario (`eliminar_tratamento`/`eliminar_fertilizacion` fan baixa lóxica: `baixa = True`). Cando se elimina o Cultivo/Parcela/Horta enteiro, os seus Tratamentos/Fertilizacións SI se borran fisicamente en cascada (non ten sentido conservalos "por baixa lóxica" se o cultivo xa non existe).
- `listar_tratamentos`/`listar_fertilizacions` excluén sempre as filas con `baixa=True`.
- Diálogos de crear conteñen só os campos obrigatorios (mesmo patrón que `crear_parcela`, que só pide nome+superficie); o resto de campos édítanse dende "Editar" (mesmo patrón que os campos SIGPAC de Parcela).
- Busca/filtro/paxinación (10 filas por páxina) en todas as pestanas novas, co mesmo patrón (`filtrar_filas`, `busca_input`/`*_select`, `refrescar_taboa`, limpeza de `taboa.selected` cando o filtro oculta a fila seleccionada) xa usado en Parcelas/Animais/Membros/Usuarios — colocado antes de calquera `if not pode_editar: return`.
- `openpyxl`/WeasyPrint non se tocan nesta iteración — reservados para a spec futura do caderno de explotación.

## Review Focus

- Eliminar unha Parcela ou Horta que teña Cultivos con Tratamentos/Fertilizacións → todo se borra en cascada sen deixar filas orfas nin violar as FK (con `PRAGMA foreign_keys=ON` activo nos tests). [Task 5]
- Eliminar un Tratamento/Fertilización individual dende a UI → a fila non desaparece da base de datos (baixa lóxica), pero deixa de aparecer en `listar_tratamentos`/`listar_fertilizacions`. [Tasks 3-4]
- Un lector (sen permiso de escritura nunha horta) pode ver/buscar/filtrar Cultivos/Tratamentos/Fertilización, pero `actualizar_*`/`eliminar_*` deben rexeitalo con `PermisoDenegadoError`. [Tasks 2-4]
- Crear un Tratamento/Fertilización pasando un `cultivo_id` que pertence a OUTRA horta distinta da que ten permiso o actor → `PermisoDenegadoError` (a comprobación de permiso resólvese a partir do `cultivo_id` recibido, non se pode enganar pasando un cultivo doutra horta). [Tasks 3-4]
- Actualizar un Cultivo/Tratamento/Fertilización pasando `baixa` (para Tratamento/Fertilización) ou `id`/`parcela_id`/`cultivo_id`/`created_at` coma campo a cambiar → `ValueError`, igual que xa fai `actualizar_parcela` cos seus campos non editables. [Tasks 2-4]

---

## Task 1: Modelos e migración

**Files:**
- Create: `src/horta/models/cultivo.py`
- Modify: `src/horta/models/__init__.py`
- Create: `alembic/versions/<hash_autoxerado>_engadir_cultivo_tratamento_fertilizacion.py` (xerado por Alembic, non escrito a man)
- Test: `tests/models/test_cultivo.py`

**Interfaces:**
- Produces: `horta.models.cultivo.Cultivo`, `horta.models.cultivo.Tratamento`, `horta.models.cultivo.Fertilizacion` — usados por todas as tarefas seguintes.

- [ ] **Step 1: Escribir o test que falla**

Crear `tests/models/test_cultivo.py`:

```python
from datetime import date

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import Horta
from horta.models.parcela import Parcela


def _crear_parcela(session) -> Parcela:
    horta = Horta(nome="A miña horta")
    session.add(horta)
    session.flush()
    parcela = Parcela(horta_id=horta.id, nome="Parcela Norte", estado="activa")
    session.add(parcela)
    session.commit()
    return parcela


def test_crear_cultivo_con_valores_por_defecto(session):
    parcela = _crear_parcela(session)

    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.commit()

    atopado = session.query(Cultivo).filter_by(especie="Tomate").one()
    assert atopado.parcela_id == parcela.id
    assert atopado.estado == "planificado"
    assert atopado.variedade is None
    assert atopado.data_sementeira is None


def test_crear_tratamento_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    tratamento = Tratamento(
        cultivo_id=cultivo.id,
        data=date(2026, 5, 1),
        praga="Mildeu",
        produto="Cobre",
        aplicador="Xabier",
    )
    session.add(tratamento)
    session.commit()

    atopado = session.query(Tratamento).filter_by(praga="Mildeu").one()
    assert atopado.baixa is False
    assert atopado.cultivo_id == cultivo.id


def test_crear_fertilizacion_con_baixa_por_defecto_false(session):
    parcela = _crear_parcela(session)
    cultivo = Cultivo(parcela_id=parcela.id, especie="Tomate")
    session.add(cultivo)
    session.flush()

    fertilizacion = Fertilizacion(
        cultivo_id=cultivo.id,
        data=date(2026, 4, 1),
        tipo="abonado_fondo",
        produto="Compost",
    )
    session.add(fertilizacion)
    session.commit()

    atopada = session.query(Fertilizacion).filter_by(produto="Compost").one()
    assert atopada.baixa is False
    assert atopada.n is None
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/models/test_cultivo.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.models.cultivo'`)

- [ ] **Step 3: Implementar `src/horta/models/cultivo.py`**

```python
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Cultivo(Base):
    __tablename__ = "cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    parcela_id: Mapped[int] = mapped_column(ForeignKey("parcela.id"))
    especie: Mapped[str] = mapped_column(String(120))
    variedade: Mapped[str | None] = mapped_column(String(120), default=None)
    data_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    data_plantacion: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_real: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(30), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Tratamento(Base):
    __tablename__ = "tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    praga: Mapped[str] = mapped_column(String(200))
    superficie_tratada: Mapped[float | None] = mapped_column(Float, default=None)
    produto: Mapped[str] = mapped_column(String(200))
    numero_rexistro_produto: Mapped[str | None] = mapped_column(String(50), default=None)
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(200), default=None)
    aplicador: Mapped[str] = mapped_column(String(200))
    equipo_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    persoas_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Fertilizacion(Base):
    __tablename__ = "fertilizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
    tipo: Mapped[str] = mapped_column(String(50))
    produto: Mapped[str] = mapped_column(String(200))
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    n: Mapped[float | None] = mapped_column(Float, default=None)
    p: Mapped[float | None] = mapped_column(Float, default=None)
    k: Mapped[float | None] = mapped_column(Float, default=None)
    carbono_organico: Mapped[float | None] = mapped_column(Float, default=None)
    micronutrientes: Mapped[str | None] = mapped_column(String(300), default=None)
    asesoramento_recibido: Mapped[str | None] = mapped_column(String(300), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

- [ ] **Step 4: Rexistrar os modelos en `src/horta/models/__init__.py`**

Substituír o ficheiro completo por:

```python
from horta.models.animal import Animal
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.usuario import RolGlobal, Usuario

__all__ = [
    "RolGlobal",
    "Usuario",
    "Horta",
    "HortaMembro",
    "RolHorta",
    "Parcela",
    "SecanoRegadio",
    "Animal",
    "Cultivo",
    "Tratamento",
    "Fertilizacion",
]
```

- [ ] **Step 5: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/models/test_cultivo.py -v`
Expected: PASS (3 tests)

- [ ] **Step 6: Xerar e revisar a migración**

Run: `uv run alembic revision --autogenerate -m "engadir cultivo, tratamento e fertilizacion"`

Abrir o ficheiro xerado en `alembic/versions/` e comprobar:
- `down_revision` apunta a `"fa79d388718f"` (a única revisión existente).
- Crea exactamente tres táboas: `cultivo`, `tratamento`, `fertilizacion`.
- Cada FK (`parcela_id`, `cultivo_id`) apunta á táboa correcta.
- Os tipos de columna coinciden cos modelos (`String`, `Float`, `Date`, `DateTime`, `Boolean`).

Se algo non coincide, correxir o ficheiro a man antes de continuar.

- [ ] **Step 7: Aplicar a migración e comprobar que funciona**

Run: `uv run alembic upgrade head`
Expected: sen erros, remata na nova revisión (`uv run alembic current` amosa o novo hash).

- [ ] **Step 8: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (todos os tests existentes, sen regresións — os tests usan `Base.metadata.create_all`, non a migración de Alembic, así que xa deberían funcionar cos modelos novos rexistrados).

- [ ] **Step 9: Commit**

```bash
git add src/horta/models/cultivo.py src/horta/models/__init__.py alembic/versions/ tests/models/test_cultivo.py
git commit -m "feat: engadir modelos Cultivo, Tratamento e Fertilizacion"
```

---

## Task 2: Servizo de Cultivos

**Files:**
- Create: `src/horta/services/cultivos.py`
- Test: `tests/services/test_cultivos.py`

**Interfaces:**
- Consumes: `horta.models.cultivo.Cultivo` (Task 1); `horta.services.hortas.comprobar_rol_horta` (xa existente).
- Produces: `crear_cultivo(session, actor, parcela_id, especie, **campos) -> Cultivo`, `actualizar_cultivo(session, actor, cultivo, **cambios) -> Cultivo`, `eliminar_cultivo(session, actor, cultivo) -> None`, `listar_cultivos(session, actor, horta_id) -> list[Cultivo]`, `CAMPOS_EDITABLES_CULTIVO: frozenset[str]`. Tasks 3/4/6/7/8 consomen `listar_cultivos`.

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_cultivos.py`:

```python
import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    listar_cultivos,
)
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela


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


def test_admin_pode_crear_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")

    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate", variedade="Negro de Santiago")

    assert cultivo.id is not None
    assert cultivo.parcela_id == parcela.id
    assert cultivo.estado == "planificado"
    assert cultivo.variedade == "Negro de Santiago"


def test_editor_pode_crear_cultivo_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_cultivo(session, bea, parcela.id, "Tomate")

    with pytest.raises(PermisoDenegadoError):
        crear_cultivo(session, carlos, parcela.id, "Repolo")


def test_crear_cultivo_en_parcela_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_cultivo(session, ana, 9999, "Tomate")


def test_listar_cultivos_devolve_os_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    outra_parcela = crear_parcela(session, ana, outra_horta.id, "Parcela de outra horta")
    crear_cultivo(session, ana, parcela.id, "Tomate")
    crear_cultivo(session, ana, outra_parcela.id, "Repolo")

    cultivos = listar_cultivos(session, ana, horta.id)

    assert [c.especie for c in cultivos] == ["Tomate"]


def test_admin_pode_actualizar_e_eliminar_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")

    actualizado = actualizar_cultivo(session, ana, cultivo, estado="sementado")
    assert actualizado.estado == "sementado"

    eliminar_cultivo(session, ana, cultivo)
    assert listar_cultivos(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_cultivo(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_cultivo(session, carlos, cultivo, estado="sementado")

    with pytest.raises(PermisoDenegadoError):
        eliminar_cultivo(session, carlos, cultivo)


@pytest.mark.parametrize("campo", ["parcela_id", "id", "created_at", "campo_inexistente"])
def test_actualizar_cultivo_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    outra_parcela = crear_parcela(session, ana, horta.id, "Outra parcela")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    id_orixinal = cultivo.id

    with pytest.raises(ValueError):
        actualizar_cultivo(session, ana, cultivo, especie="Cambiado", **{campo: outra_parcela.id})

    session.refresh(cultivo)
    assert cultivo.id == id_orixinal
    assert cultivo.parcela_id == parcela.id
    assert cultivo.especie == "Tomate"
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_cultivos.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.cultivos'`)

- [ ] **Step 3: Implementar `src/horta/services/cultivos.py`**

```python
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_cultivo. Queda fóra id,
# parcela_id e created_at: mover un cultivo a outra parcela saltaría o
# control de permisos, que se fai coa parcela_id actual.
CAMPOS_EDITABLES_CULTIVO = frozenset(
    {
        "especie",
        "variedade",
        "data_sementeira",
        "data_plantacion",
        "data_colleita_prevista",
        "data_colleita_real",
        "cantidade",
        "unidade",
        "notas",
        "estado",
    }
)


def _horta_id_da_parcela(session: Session, parcela_id: int) -> int | None:
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()


def crear_cultivo(
    session: Session,
    actor: Usuario,
    parcela_id: int,
    especie: str,
    **campos: Any,
) -> Cultivo:
    horta_id = _horta_id_da_parcela(session, parcela_id)
    if horta_id is None:
        raise ValueError("Esa parcela non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "planificado")
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, estado=estado, **campos)
    session.add(cultivo)
    session.commit()
    return cultivo


def actualizar_cultivo(
    session: Session,
    actor: Usuario,
    cultivo: Cultivo,
    **cambios: Any,
) -> Cultivo:
    non_editables = set(cambios) - CAMPOS_EDITABLES_CULTIVO
    if non_editables:
        raise ValueError(f"Campos non editables nun cultivo: {', '.join(sorted(non_editables))}")
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    session.commit()
    return cultivo


def eliminar_cultivo(session: Session, actor: Usuario, cultivo: Cultivo) -> None:
    """Elimina o cultivo e, en cascada, os seus tratamentos e fertilizacións.

    A diferenza de eliminar_tratamento/eliminar_fertilizacion (baixa lóxica),
    aquí bórranse fisicamente: non ten sentido conservar por baixa lóxica un
    tratamento cuxo cultivo xa non existe.
    """
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
        session.delete(tratamento)
    for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
        session.delete(fertilizacion)
    session.flush()
    session.delete(cultivo)
    session.commit()


def listar_cultivos(session: Session, actor: Usuario, horta_id: int) -> list[Cultivo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Cultivo)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
        .order_by(Cultivo.especie)
        .all()
    )
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_cultivos.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/cultivos.py tests/services/test_cultivos.py
git commit -m "feat: engadir servizo de Cultivos"
```

---

## Task 3: Servizo de Tratamentos (con baixa lóxica)

**Files:**
- Create: `src/horta/services/tratamentos.py`
- Test: `tests/services/test_tratamentos.py`

**Interfaces:**
- Consumes: `horta.models.cultivo.{Cultivo, Tratamento}` (Task 1); `horta.services.cultivos.crear_cultivo` (Task 2, só nos tests, para preparar datos).
- Produces: `crear_tratamento(session, actor, cultivo_id, data, praga, produto, aplicador, **campos) -> Tratamento`, `actualizar_tratamento(session, actor, tratamento, **cambios) -> Tratamento`, `eliminar_tratamento(session, actor, tratamento) -> None` (baixa lóxica), `listar_tratamentos(session, actor, horta_id) -> list[Tratamento]`, `CAMPOS_EDITABLES_TRATAMENTO: frozenset[str]`. Task 7 consome todo isto.

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_tratamentos.py`:

```python
from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.tratamentos import (
    actualizar_tratamento,
    crear_tratamento,
    eliminar_tratamento,
    listar_tratamentos,
)


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


def _crear_cultivo(session, actor, horta_id):
    parcela = crear_parcela(session, actor, horta_id, "Parcela Norte")
    return crear_cultivo(session, actor, parcela.id, "Tomate")


def test_admin_pode_crear_tratamento(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )

    assert tratamento.id is not None
    assert tratamento.cultivo_id == cultivo.id
    assert tratamento.baixa is False


def test_editor_pode_crear_tratamento_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_tratamento(session, bea, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Bea")

    with pytest.raises(PermisoDenegadoError):
        crear_tratamento(session, carlos, cultivo.id, date(2026, 5, 2), "Pulgón", "Xabón", "Carlos")


def test_crear_tratamento_en_cultivo_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_tratamento(session, ana, 9999, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier")


def test_crear_tratamento_en_cultivo_doutra_horta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta_ana = crear_horta(session, ana, "Horta de Ana")
    horta_carlos = crear_horta(session, carlos, "Horta de Carlos")
    cultivo_de_ana = _crear_cultivo(session, ana, horta_ana.id)
    engadir_membro(session, carlos, horta_carlos.id, ana, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        crear_tratamento(
            session, carlos, cultivo_de_ana.id, date(2026, 5, 1), "Mildeu", "Cobre", "Carlos"
        )


def test_eliminar_tratamento_e_baixa_loxica_non_borrado_fisico(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )

    eliminar_tratamento(session, ana, tratamento)

    session.refresh(tratamento)
    assert tratamento.baixa is True
    assert listar_tratamentos(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_tratamento(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_tratamento(session, carlos, tratamento, praga="Pulgón")

    with pytest.raises(PermisoDenegadoError):
        eliminar_tratamento(session, carlos, tratamento)


@pytest.mark.parametrize("campo", ["cultivo_id", "id", "created_at", "baixa", "campo_inexistente"])
def test_actualizar_tratamento_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    outro_cultivo = _crear_cultivo(session, ana, horta.id)
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    id_orixinal = tratamento.id

    valor = outro_cultivo.id if campo == "cultivo_id" else True
    with pytest.raises(ValueError):
        actualizar_tratamento(session, ana, tratamento, praga="Cambiado", **{campo: valor})

    session.refresh(tratamento)
    assert tratamento.id == id_orixinal
    assert tratamento.cultivo_id == cultivo.id
    assert tratamento.praga == "Mildeu"
    assert tratamento.baixa is False
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_tratamentos.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.tratamentos'`)

- [ ] **Step 3: Implementar `src/horta/services/tratamentos.py`**

```python
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra cultivo_id, id, created_at e baixa: baixa só se cambia dende
# eliminar_tratamento (baixa lóxica), nunca dende unha actualización xenérica.
CAMPOS_EDITABLES_TRATAMENTO = frozenset(
    {
        "data",
        "praga",
        "superficie_tratada",
        "produto",
        "numero_rexistro_produto",
        "dose",
        "eficacia",
        "aplicador",
        "equipo_aplicador",
        "persoas_asesoramento",
        "notas",
    }
)


def _horta_id_do_cultivo(session: Session, cultivo_id: int) -> int | None:
    return (
        session.query(Parcela.horta_id)
        .join(Cultivo, Cultivo.parcela_id == Parcela.id)
        .filter(Cultivo.id == cultivo_id)
        .scalar()
    )


def crear_tratamento(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    data: Any,
    praga: str,
    produto: str,
    aplicador: str,
    **campos: Any,
) -> Tratamento:
    horta_id = _horta_id_do_cultivo(session, cultivo_id)
    if horta_id is None:
        raise ValueError("Ese cultivo non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    tratamento = Tratamento(
        cultivo_id=cultivo_id,
        data=data,
        praga=praga,
        produto=produto,
        aplicador=aplicador,
        **campos,
    )
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento(
    session: Session,
    actor: Usuario,
    tratamento: Tratamento,
    **cambios: Any,
) -> Tratamento:
    non_editables = set(cambios) - CAMPOS_EDITABLES_TRATAMENTO
    if non_editables:
        raise ValueError(f"Campos non editables nun tratamento: {', '.join(sorted(non_editables))}")
    horta_id = _horta_id_do_cultivo(session, tratamento.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo deste tratamento xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(tratamento, campo, valor)
    session.commit()
    return tratamento


def eliminar_tratamento(session: Session, actor: Usuario, tratamento: Tratamento) -> None:
    """Dá de baixa o tratamento (baixa lóxica).

    Nunca se borra fisicamente: a normativa esixe conservar estes rexistros
    un mínimo de 3 anos (README §22). Deixa de aparecer en listar_tratamentos,
    pero a fila segue na base de datos.
    """
    horta_id = _horta_id_do_cultivo(session, tratamento.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo deste tratamento xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos(session: Session, actor: Usuario, horta_id: int) -> list[Tratamento]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tratamento)
        .join(Cultivo, Tratamento.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id, Tratamento.baixa.is_(False))
        .order_by(Tratamento.data.desc())
        .all()
    )
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_tratamentos.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/tratamentos.py tests/services/test_tratamentos.py
git commit -m "feat: engadir servizo de Tratamentos con baixa lóxica"
```

---

## Task 4: Servizo de Fertilización (con baixa lóxica)

**Files:**
- Create: `src/horta/services/fertilizacions.py`
- Test: `tests/services/test_fertilizacions.py`

**Interfaces:**
- Consumes: `horta.models.cultivo.{Cultivo, Fertilizacion}` (Task 1); `horta.services.cultivos.crear_cultivo` (Task 2, só nos tests).
- Produces: `crear_fertilizacion(session, actor, cultivo_id, data, tipo, produto, **campos) -> Fertilizacion`, `actualizar_fertilizacion(session, actor, fertilizacion, **cambios) -> Fertilizacion`, `eliminar_fertilizacion(session, actor, fertilizacion) -> None` (baixa lóxica), `listar_fertilizacions(session, actor, horta_id) -> list[Fertilizacion]`, `CAMPOS_EDITABLES_FERTILIZACION: frozenset[str]`. Task 8 consome todo isto.

Este servizo é o mesmo patrón exacto que a Task 3 (Tratamentos), coa entidade Fertilizacion.

- [ ] **Step 1: Escribir os tests que fallan**

Crear `tests/services/test_fertilizacions.py`:

```python
from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.fertilizacions import (
    actualizar_fertilizacion,
    crear_fertilizacion,
    eliminar_fertilizacion,
    listar_fertilizacions,
)
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela


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


def _crear_cultivo(session, actor, horta_id):
    parcela = crear_parcela(session, actor, horta_id, "Parcela Norte")
    return crear_cultivo(session, actor, parcela.id, "Tomate")


def test_admin_pode_crear_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)

    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )

    assert fertilizacion.id is not None
    assert fertilizacion.cultivo_id == cultivo.id
    assert fertilizacion.baixa is False


def test_editor_pode_crear_fertilizacion_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_fertilizacion(session, bea, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost")

    with pytest.raises(PermisoDenegadoError):
        crear_fertilizacion(session, carlos, cultivo.id, date(2026, 4, 2), "cobertoira", "Xurro")


def test_crear_fertilizacion_en_cultivo_inexistente_falla(session):
    ana = _crear_usuario(session, "ana@example.com")
    crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError):
        crear_fertilizacion(session, ana, 9999, date(2026, 4, 1), "abonado_fondo", "Compost")


def test_crear_fertilizacion_en_cultivo_doutra_horta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta_ana = crear_horta(session, ana, "Horta de Ana")
    horta_carlos = crear_horta(session, carlos, "Horta de Carlos")
    cultivo_de_ana = _crear_cultivo(session, ana, horta_ana.id)
    engadir_membro(session, carlos, horta_carlos.id, ana, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        crear_fertilizacion(
            session, carlos, cultivo_de_ana.id, date(2026, 4, 1), "abonado_fondo", "Compost"
        )


def test_eliminar_fertilizacion_e_baixa_loxica_non_borrado_fisico(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )

    eliminar_fertilizacion(session, ana, fertilizacion)

    session.refresh(fertilizacion)
    assert fertilizacion.baixa is True
    assert listar_fertilizacions(session, ana, horta.id) == []


def test_lector_non_pode_actualizar_nin_eliminar_fertilizacion(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        actualizar_fertilizacion(session, carlos, fertilizacion, produto="Cambiado")

    with pytest.raises(PermisoDenegadoError):
        eliminar_fertilizacion(session, carlos, fertilizacion)


@pytest.mark.parametrize("campo", ["cultivo_id", "id", "created_at", "baixa", "campo_inexistente"])
def test_actualizar_fertilizacion_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    cultivo = _crear_cultivo(session, ana, horta.id)
    outro_cultivo = _crear_cultivo(session, ana, horta.id)
    fertilizacion = crear_fertilizacion(
        session, ana, cultivo.id, date(2026, 4, 1), "abonado_fondo", "Compost"
    )
    id_orixinal = fertilizacion.id

    valor = outro_cultivo.id if campo == "cultivo_id" else True
    with pytest.raises(ValueError):
        actualizar_fertilizacion(session, ana, fertilizacion, produto="Cambiado", **{campo: valor})

    session.refresh(fertilizacion)
    assert fertilizacion.id == id_orixinal
    assert fertilizacion.cultivo_id == cultivo.id
    assert fertilizacion.produto == "Compost"
    assert fertilizacion.baixa is False
```

- [ ] **Step 2: Executar os tests e comprobar que fallan**

Run: `uv run pytest tests/services/test_fertilizacions.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'horta.services.fertilizacions'`)

- [ ] **Step 3: Implementar `src/horta/services/fertilizacions.py`**

```python
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Fertilizacion
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra cultivo_id, id, created_at e baixa: baixa só se cambia dende
# eliminar_fertilizacion (baixa lóxica), nunca dende unha actualización xenérica.
CAMPOS_EDITABLES_FERTILIZACION = frozenset(
    {
        "data",
        "superficie",
        "tipo",
        "produto",
        "dose",
        "n",
        "p",
        "k",
        "carbono_organico",
        "micronutrientes",
        "asesoramento_recibido",
        "notas",
    }
)


def _horta_id_do_cultivo(session: Session, cultivo_id: int) -> int | None:
    return (
        session.query(Parcela.horta_id)
        .join(Cultivo, Cultivo.parcela_id == Parcela.id)
        .filter(Cultivo.id == cultivo_id)
        .scalar()
    )


def crear_fertilizacion(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    data: Any,
    tipo: str,
    produto: str,
    **campos: Any,
) -> Fertilizacion:
    horta_id = _horta_id_do_cultivo(session, cultivo_id)
    if horta_id is None:
        raise ValueError("Ese cultivo non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    fertilizacion = Fertilizacion(
        cultivo_id=cultivo_id,
        data=data,
        tipo=tipo,
        produto=produto,
        **campos,
    )
    session.add(fertilizacion)
    session.commit()
    return fertilizacion


def actualizar_fertilizacion(
    session: Session,
    actor: Usuario,
    fertilizacion: Fertilizacion,
    **cambios: Any,
) -> Fertilizacion:
    non_editables = set(cambios) - CAMPOS_EDITABLES_FERTILIZACION
    if non_editables:
        raise ValueError(
            f"Campos non editables nunha fertilización: {', '.join(sorted(non_editables))}"
        )
    horta_id = _horta_id_do_cultivo(session, fertilizacion.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo desta fertilización xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(fertilizacion, campo, valor)
    session.commit()
    return fertilizacion


def eliminar_fertilizacion(session: Session, actor: Usuario, fertilizacion: Fertilizacion) -> None:
    """Dá de baixa a fertilización (baixa lóxica).

    Nunca se borra fisicamente: a normativa esixe conservar estes rexistros
    un mínimo de 3 anos (README §22). Deixa de aparecer en
    listar_fertilizacions, pero a fila segue na base de datos.
    """
    horta_id = _horta_id_do_cultivo(session, fertilizacion.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo desta fertilización xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    fertilizacion.baixa = True
    session.commit()


def listar_fertilizacions(session: Session, actor: Usuario, horta_id: int) -> list[Fertilizacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Fertilizacion)
        .join(Cultivo, Fertilizacion.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id, Fertilizacion.baixa.is_(False))
        .order_by(Fertilizacion.data.desc())
        .all()
    )
```

- [ ] **Step 4: Executar os tests e comprobar que pasan**

Run: `uv run pytest tests/services/test_fertilizacions.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións)

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/fertilizacions.py tests/services/test_fertilizacions.py
git commit -m "feat: engadir servizo de Fertilización con baixa lóxica"
```

---

## Task 5: Cascada de eliminación en Parcela e Horta

**Files:**
- Modify: `src/horta/services/parcelas.py`
- Modify: `src/horta/services/hortas.py`
- Test: engadir a `tests/services/test_parcelas.py` e `tests/services/test_hortas.py` (ficheiros existentes)

**Interfaces:**
- Consumes: `horta.models.cultivo.{Cultivo, Tratamento, Fertilizacion}` (Task 1); `horta.services.cultivos.crear_cultivo`, `horta.services.tratamentos.crear_tratamento`, `horta.services.fertilizacions.crear_fertilizacion` (Tasks 2-4, só nos tests).

- [ ] **Step 1: Escribir o test que falla (cascada en eliminar_parcela)**

`tests/services/test_parcelas.py` comeza hoxe con:

```python
import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
```

Substituír por (engade `date`, `Cultivo`/`Tratamento`, `crear_cultivo` e `crear_tratamento`, mantendo a orde alfabética xa usada):

```python
from datetime import date

import pytest

from horta.models.cultivo import Cultivo, Tratamento
from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.tratamentos import crear_tratamento
```

Engadir o test:

```python
def test_eliminar_parcela_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_parcela(session, ana, parcela)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None
```

- [ ] **Step 2: Executar o test e comprobar que falla**

Run: `uv run pytest tests/services/test_parcelas.py::test_eliminar_parcela_borra_en_cascada_cultivos_e_tratamentos -v`
Expected: FAIL (`IntegrityError` — a FK `cultivo.parcela_id` impide borrar a parcela mentres o cultivo siga existindo, porque `PRAGMA foreign_keys=ON` está activo nos tests).

- [ ] **Step 3: Actualizar `eliminar_parcela` en `src/horta/services/parcelas.py`**

Engadir o import ao principio do ficheiro, antes de `from horta.models.horta import RolHorta` (orde alfabética: `cultivo`, `horta`, `parcela`, `usuario`):

```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
```

Substituír:

```python
def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(parcela)
    session.commit()
```

por:

```python
def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    cultivos = session.query(Cultivo).filter_by(parcela_id=parcela.id).all()
    for cultivo in cultivos:
        for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
            session.delete(tratamento)
        for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
            session.delete(fertilizacion)
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()
    session.delete(parcela)
    session.commit()
```

- [ ] **Step 4: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/services/test_parcelas.py -v`
Expected: PASS (todos, incluído o novo)

- [ ] **Step 5: Escribir o test que falla (cascada en eliminar_horta)**

`tests/services/test_hortas.py` xa importa `crear_parcela`, e usa `import datetime` (non `from datetime import date`) — as datas escríbense coma `datetime.date(...)`. Engadir estes catro imports novos, mantendo esa mesma convención e a orde alfabética xa usada no ficheiro:

Substituír:

```python
from horta.models.animal import Animal
from horta.models.horta import Horta, HortaMembro, RolHorta
```

por:

```python
from horta.models.animal import Animal
from horta.models.cultivo import Cultivo, Tratamento
from horta.models.horta import Horta, HortaMembro, RolHorta
```

Substituír:

```python
from horta.services.animais import crear_animal
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
```

por:

```python
from horta.services.animais import crear_animal
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
```

Substituír:

```python
from horta.services.parcelas import crear_parcela
```

por:

```python
from horta.services.parcelas import crear_parcela
from horta.services.tratamentos import crear_tratamento
```

Engadir o test (`_crear_usuario` xa existe neste ficheiro coa mesma sinatura usada no resto do plan):

```python
def test_eliminar_horta_borra_en_cascada_cultivos_e_tratamentos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    tratamento = crear_tratamento(
        session, ana, cultivo.id, datetime.date(2026, 5, 1), "Mildeu", "Cobre", "Xabier"
    )
    cultivo_id, tratamento_id = cultivo.id, tratamento.id

    eliminar_horta(session, ana, horta)

    assert session.get(Cultivo, cultivo_id) is None
    assert session.get(Tratamento, tratamento_id) is None
```

- [ ] **Step 6: Executar o test e comprobar que falla**

Run: `uv run pytest tests/services/test_hortas.py::test_eliminar_horta_borra_en_cascada_cultivos_e_tratamentos -v`
Expected: FAIL (`IntegrityError`, mesmo motivo que na Step 2).

- [ ] **Step 7: Actualizar `eliminar_horta` en `src/horta/services/hortas.py`**

Engadir o import ao principio do ficheiro (despois de `from horta.models.animal import Animal`):

```python
from horta.models.animal import Animal
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Substituír o corpo de `eliminar_horta`:

```python
def eliminar_horta(session: Session, actor: Usuario, horta: Horta) -> None:
    """Elimina a horta e todo o que dependa dela (parcelas, animais, membros).

    Non hai borrado en cascada a nivel de base de datos (sen relacións
    SQLAlchemy nin FKs ON DELETE CASCADE), así que hai que borrar
    explicitamente os rexistros dependentes antes da propia horta.
    """
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    parcelas = session.query(Parcela).filter_by(horta_id=horta.id).all()
    parcela_ids = [p.id for p in parcelas]
    cultivos = (
        session.query(Cultivo).filter(Cultivo.parcela_id.in_(parcela_ids)).all()
        if parcela_ids
        else []
    )
    cultivo_ids = [c.id for c in cultivos]
    if cultivo_ids:
        for tratamento in session.query(Tratamento).filter(Tratamento.cultivo_id.in_(cultivo_ids)).all():
            session.delete(tratamento)
        for fertilizacion in (
            session.query(Fertilizacion).filter(Fertilizacion.cultivo_id.in_(cultivo_ids)).all()
        ):
            session.delete(fertilizacion)
    for cultivo in cultivos:
        session.delete(cultivo)
    for parcela in parcelas:
        session.delete(parcela)
    for animal in session.query(Animal).filter_by(horta_id=horta.id).all():
        session.delete(animal)
    for membro in session.query(HortaMembro).filter_by(horta_id=horta.id).all():
        session.delete(membro)
    # SQLAlchemy non ten relationship() entre estes modelos, así que non hai
    # información de dependencia para ordenar o DELETE automaticamente. Sen
    # este flush, os borrados poden enviarse na orde inversa (horta antes dos
    # seus fillos), o que falla en calquera BD que comprobe as FKs.
    session.flush()
    session.delete(horta)
    session.commit()
```

- [ ] **Step 8: Executar o test e comprobar que pasa**

Run: `uv run pytest tests/services/test_hortas.py -v`
Expected: PASS (todos, incluído o novo)

- [ ] **Step 9: Executar a suite completa, ruff e mypy**

Run: `uv run pytest -v` → PASS sen regresións.
Run: `uv run ruff check src tests` → sen erros.
Run: `uv run mypy src` → sen erros.

- [ ] **Step 10: Commit**

```bash
git add src/horta/services/parcelas.py src/horta/services/hortas.py tests/services/test_parcelas.py tests/services/test_hortas.py
git commit -m "fix: cascada de eliminación de cultivos/tratamentos/fertilizacións en Parcela e Horta"
```

---

## Task 6: Pestana de Cultivos na UI

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.services.cultivos.{crear_cultivo, actualizar_cultivo, eliminar_cultivo, listar_cultivos}` (Task 2); `horta.ui.filtros.filtrar_filas` (xa existente).
- Produces: constantes de módulo `_ESTADOS_CULTIVO`, `_UNIDADES_CULTIVO` — non consumidas por outras tarefas deste plan (Tratamentos/Fertilización non usan estado/unidade de Cultivo).

- [ ] **Step 1: Engadir os imports e as constantes de módulo**

Inserir entre o import de `animais` e o de `errors` (orde alfabética dos módulos de servizo: `animais`, `cultivos`, `errors`, `hortas`, `parcelas`), de forma que quede así:

```python
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    listar_cultivos,
)
from horta.services.errors import PermisoDenegadoError
```

Engadir despois de `_ROLES_HORTA = ("admin", "editor", "lector")`:

```python
_ROLES_HORTA = ("admin", "editor", "lector")

_ESTADOS_CULTIVO = ("planificado", "sementado", "plantado", "colleitado", "finalizado")
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")
```

- [ ] **Step 2: Cargar os cultivos na páxina e engadir a pestana**

Dentro de `horta_detalle_page`, substituír:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
```

por:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
```

Substituír:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

por:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

- [ ] **Step 3: Engadir a función `_seccion_cultivos`**

Engadir esta función nova despois de `_seccion_parcelas` remata e antes de `def _seccion_animais(...)`:

```python
def _seccion_cultivos(
    horta_id: int, cultivos: list, parcelas: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}

    if pode_editar:
        with ui.dialog() as dialog_novo_cultivo, ui.card():
            ui.label("Novo cultivo").classes("text-md font-bold")
            parcela_select = ui.select({p.id: p.nome for p in parcelas}, label="Parcela")
            especie_input = ui.input("Especie")
            variedade_input = ui.input("Variedade (opcional)")

            def crear() -> None:
                if not (parcela_select.value and especie_input.value):
                    ui.notify("Parcela e especie son obrigatorias", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_cultivo(
                            session,
                            actor_actual,
                            parcela_select.value,
                            especie_input.value,
                            variedade=variedade_input.value or None,
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_cultivo.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Cultivos").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Novo cultivo", icon="add", on_click=dialog_novo_cultivo.open)

    todas_as_filas = [
        {
            "id": c.id,
            "parcela": parcelas_por_id.get(c.parcela_id, "?"),
            "especie": c.especie,
            "variedade": c.variedade or "",
            "estado": c.estado,
        }
        for c in cultivos
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        estado_select = ui.select(
            ["Todos", *_ESTADOS_CULTIVO], label="Estado", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "parcela", "label": "Parcela", "field": "parcela"},
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "variedade", "label": "Variedade", "field": "variedade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        estado_filtro = None if estado_select.value == "Todos" else estado_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["parcela", "especie", "variedade", "estado"],
            {"estado": estado_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    estado_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar o cultivo «{taboa.selected[0]['especie']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar cultivo").classes("text-md font-bold")
        especie_edit = ui.input("Especie")
        variedade_edit = ui.input("Variedade")
        cantidade_edit = ui.number("Cantidade")
        unidade_edit = ui.select(list(_UNIDADES_CULTIVO), label="Unidade")
        data_sementeira_edit = ui.input("Data sementeira (AAAA-MM-DD)")
        data_plantacion_edit = ui.input("Data plantación (AAAA-MM-DD)")
        data_colleita_prevista_edit = ui.input("Data colleita prevista (AAAA-MM-DD)")
        data_colleita_real_edit = ui.input("Data colleita real (AAAA-MM-DD)")
        notas_edit = ui.textarea("Notas")
        estado_edit = ui.select(list(_ESTADOS_CULTIVO), label="Estado", value="planificado")

        def _parsear_data(texto: str) -> Any:
            if not texto:
                return None
            try:
                return date.fromisoformat(texto)
            except ValueError as erro:
                raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

        def gardar() -> None:
            if not taboa.selected:
                return
            cultivo_id = taboa.selected[0]["id"]
            if not especie_edit.value:
                ui.notify("A especie é obrigatoria", type="negative")
                return
            try:
                cambios = dict(
                    especie=especie_edit.value,
                    variedade=variedade_edit.value or None,
                    cantidade=cantidade_edit.value,
                    unidade=unidade_edit.value,
                    data_sementeira=_parsear_data(data_sementeira_edit.value),
                    data_plantacion=_parsear_data(data_plantacion_edit.value),
                    data_colleita_prevista=_parsear_data(data_colleita_prevista_edit.value),
                    data_colleita_real=_parsear_data(data_colleita_real_edit.value),
                    notas=notas_edit.value or None,
                    estado=estado_edit.value,
                )
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        c
                        for c in listar_cultivos(session, actor_actual, horta_id)
                        if c.id == cultivo_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese cultivo xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session, lambda: actualizar_cultivo(session, actor_actual, obxectivo, **cambios)
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        cultivo_id = fila["id"]
        cultivo_completo = next((c for c in cultivos if c.id == cultivo_id), None)
        if cultivo_completo is None:
            return
        especie_edit.value = cultivo_completo.especie
        variedade_edit.value = cultivo_completo.variedade or ""
        cantidade_edit.value = cultivo_completo.cantidade
        unidade_edit.value = cultivo_completo.unidade
        data_sementeira_edit.value = (
            cultivo_completo.data_sementeira.isoformat() if cultivo_completo.data_sementeira else ""
        )
        data_plantacion_edit.value = (
            cultivo_completo.data_plantacion.isoformat() if cultivo_completo.data_plantacion else ""
        )
        data_colleita_prevista_edit.value = (
            cultivo_completo.data_colleita_prevista.isoformat()
            if cultivo_completo.data_colleita_prevista
            else ""
        )
        data_colleita_real_edit.value = (
            cultivo_completo.data_colleita_real.isoformat()
            if cultivo_completo.data_colleita_real
            else ""
        )
        notas_edit.value = cultivo_completo.notas or ""
        estado_edit.value = cultivo_completo.estado
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        cultivo_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (c for c in listar_cultivos(session, actor_actual, horta_id) if c.id == cultivo_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese cultivo xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_cultivo(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()
```

**Nota importante:** `abrir_editar` len o cultivo completo dende a lista `cultivos` (o parámetro da función, cargado unha soa vez ao abrir a páxina) buscando por `id`, en vez de reconsultar a BD — porque as filas da táboa (`taboa.selected[0]`) só teñen os catro campos amosados na táboa (parcela/especie/variedade/estado), non todos os campos do cultivo que fan falla para preenchelos no diálogo de edición. Isto é distinto do patrón de Parcelas/Animais, onde todos os campos editables xa estaban na fila da táboa.

O ficheiro aínda non importa `Any` (necesario pola sinatura de `_parsear_data`). Engadir `from typing import Any` despois de `from datetime import date` (orde alfabética entre módulos da stdlib: `datetime`, `typing`):

```python
from __future__ import annotations

from datetime import date
from typing import Any

from loguru import logger
```

- [ ] **Step 4: Executar a suite completa**

Run: `uv run pytest -v`
Expected: PASS (sen regresións — esta tarefa non engade tests novos, as páxinas NiceGUI non se testean unitariamente)

- [ ] **Step 5: Ruff e mypy**

Run: `uv run ruff check src tests`
Expected: sen erros

Run: `uv run mypy src`
Expected: sen erros

- [ ] **Step 6: Verificación manual**

Run: `uv run python src/horta/main.py` (en segundo plano)

1. Entrar nunha horta, ir á pestana "Cultivos". Crear un cultivo novo (parcela + especie).
2. Buscar por especie, filtrar por Estado, combinar os dous.
3. Editar o cultivo creado: cambiar variedade, engadir unha data de sementeira en formato `AAAA-MM-DD`, cambiar o estado, gardar, e confirmar que os cambios se reflicten.
4. Probar unha data mal formada (p.ex. "31/12/2026") no diálogo de editar e confirmar que amosa un aviso claro en vez de petar.
5. Eliminar o cultivo de proba.

Parar o servidor despois de verificar.

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir pestana de Cultivos"
```

---

## Task 7: Pestana de Tratamentos na UI

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.services.tratamentos.{crear_tratamento, actualizar_tratamento, eliminar_tratamento, listar_tratamentos}` (Task 3); `horta.ui.filtros.filtrar_filas`.

- [ ] **Step 1: Engadir os imports e cargar os tratamentos**

Inserir despois do import de `parcelas` e antes de `from horta.ui.accions import executar_accion` (orde alfabética dos módulos de servizo: `animais`, `cultivos`, `errors`, `hortas`, `parcelas`, `tratamentos` — `fertilizacions` chegará na Task 8, entre `errors` e `hortas`), de forma que quede así:

```python
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.services.tratamentos import (
    actualizar_tratamento,
    crear_tratamento,
    eliminar_tratamento,
    listar_tratamentos,
)
from horta.ui.accions import executar_accion
```

Dentro de `horta_detalle_page`, substituír:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
```

por:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        tratamentos = listar_tratamentos(session, actor, horta_id)
```

- [ ] **Step 2: Engadir a pestana de Tratamentos**

Substituír:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

por:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_tratamentos = ui.tab("Tratamentos")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_tratamentos):
            _seccion_tratamentos(horta_id, tratamentos, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

- [ ] **Step 3: Engadir a función `_seccion_tratamentos`**

Engadir esta función despois de `_seccion_cultivos` remata e antes de `def _seccion_animais(...)`:

```python
def _seccion_tratamentos(
    horta_id: int, tratamentos: list, cultivos: list, parcelas: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}
    etiquetas_cultivo = {
        c.id: f"{c.especie} — {parcelas_por_id.get(c.parcela_id, '?')}" for c in cultivos
    }

    def _parsear_data(texto: str) -> Any:
        if not texto:
            raise ValueError("A data é obrigatoria")
        try:
            return date.fromisoformat(texto)
        except ValueError as erro:
            raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

    if pode_editar:
        with ui.dialog() as dialog_novo_tratamento, ui.card():
            ui.label("Novo tratamento").classes("text-md font-bold")
            cultivo_select = ui.select(etiquetas_cultivo, label="Cultivo")
            data_input = ui.input("Data (AAAA-MM-DD)")
            praga_input = ui.input("Praga")
            produto_input = ui.input("Produto")
            aplicador_input = ui.input("Aplicador")

            def crear() -> None:
                if not (
                    cultivo_select.value
                    and data_input.value
                    and praga_input.value
                    and produto_input.value
                    and aplicador_input.value
                ):
                    ui.notify("Cultivo, data, praga, produto e aplicador son obrigatorios", type="negative")
                    return
                try:
                    data_valor = _parsear_data(data_input.value)
                except ValueError as erro:
                    ui.notify(str(erro), type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_tratamento(
                            session,
                            actor_actual,
                            cultivo_select.value,
                            data_valor,
                            praga_input.value,
                            produto_input.value,
                            aplicador_input.value,
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_tratamento.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Tratamentos").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Novo tratamento", icon="add", on_click=dialog_novo_tratamento.open)

    todas_as_filas = [
        {
            "id": t.id,
            "cultivo": etiquetas_cultivo.get(t.cultivo_id, "?"),
            "data": t.data.isoformat(),
            "praga": t.praga,
            "produto": t.produto,
            "aplicador": t.aplicador,
        }
        for t in tratamentos
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")

    taboa = (
        ui.table(
            columns=[
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
                {"name": "data", "label": "Data", "field": "data"},
                {"name": "praga", "label": "Praga", "field": "praga"},
                {"name": "produto", "label": "Produto", "field": "produto"},
                {"name": "aplicador", "label": "Aplicador", "field": "aplicador"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["cultivo", "data", "praga", "produto", "aplicador"],
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar o tratamento de «{taboa.selected[0]['praga']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar tratamento").classes("text-md font-bold")
        data_edit = ui.input("Data (AAAA-MM-DD)")
        praga_edit = ui.input("Praga")
        produto_edit = ui.input("Produto")
        numero_rexistro_edit = ui.input("Nº de rexistro do produto")
        dose_edit = ui.input("Dose")
        superficie_edit = ui.number("Superficie tratada (m²)")
        eficacia_edit = ui.input("Valoración da eficacia")
        aplicador_edit = ui.input("Aplicador")
        equipo_aplicador_edit = ui.input("Equipo aplicador")
        persoas_asesoramento_edit = ui.input("Persoas de asesoramento")
        notas_edit = ui.textarea("Notas")

        def gardar() -> None:
            if not taboa.selected:
                return
            tratamento_id = taboa.selected[0]["id"]
            if not (praga_edit.value and produto_edit.value and aplicador_edit.value):
                ui.notify("Praga, produto e aplicador son obrigatorios", type="negative")
                return
            try:
                data_valor = _parsear_data(data_edit.value)
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        t
                        for t in listar_tratamentos(session, actor_actual, horta_id)
                        if t.id == tratamento_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese tratamento xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_tratamento(
                        session,
                        actor_actual,
                        obxectivo,
                        data=data_valor,
                        praga=praga_edit.value,
                        produto=produto_edit.value,
                        numero_rexistro_produto=numero_rexistro_edit.value or None,
                        dose=dose_edit.value or None,
                        superficie_tratada=superficie_edit.value,
                        eficacia=eficacia_edit.value or None,
                        aplicador=aplicador_edit.value,
                        equipo_aplicador=equipo_aplicador_edit.value or None,
                        persoas_asesoramento=persoas_asesoramento_edit.value or None,
                        notas=notas_edit.value or None,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        tratamento_id = taboa.selected[0]["id"]
        tratamento_completo = next((t for t in tratamentos if t.id == tratamento_id), None)
        if tratamento_completo is None:
            return
        data_edit.value = tratamento_completo.data.isoformat()
        praga_edit.value = tratamento_completo.praga
        produto_edit.value = tratamento_completo.produto
        numero_rexistro_edit.value = tratamento_completo.numero_rexistro_produto or ""
        dose_edit.value = tratamento_completo.dose or ""
        superficie_edit.value = tratamento_completo.superficie_tratada
        eficacia_edit.value = tratamento_completo.eficacia or ""
        aplicador_edit.value = tratamento_completo.aplicador
        equipo_aplicador_edit.value = tratamento_completo.equipo_aplicador or ""
        persoas_asesoramento_edit.value = tratamento_completo.persoas_asesoramento or ""
        notas_edit.value = tratamento_completo.notas or ""
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        tratamento_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (
                    t
                    for t in listar_tratamentos(session, actor_actual, horta_id)
                    if t.id == tratamento_id
                ),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese tratamento xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_tratamento(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()
```

**Nota:** `filtrar_filas` chámase aquí sen o cuarto argumento (`filtros_estruturados`) porque Tratamentos non ten selector estruturado (só busca de texto) — a sinatura de `filtrar_filas` xa acepta `filtros_estruturados=None` por defecto (Task 1 do plan anterior de busca/filtros).

- [ ] **Step 4: Executar a suite completa, ruff e mypy**

Run: `uv run pytest -v` → PASS sen regresións.
Run: `uv run ruff check src tests` → sen erros.
Run: `uv run mypy src` → sen erros.

- [ ] **Step 5: Verificación manual**

1. Crear un cultivo de proba (se non hai ningún xa) e ir á pestana "Tratamentos".
2. Crear un tratamento novo (cultivo + data + praga + produto + aplicador).
3. Buscar por praga/produto.
4. Editar o tratamento (engadir número de rexistro, dose, eficacia).
5. Eliminar o tratamento — confirmar na UI que desaparece da táboa, e comprobar (p.ex. cun script rápido `uv run python -c "..."`) que a fila segue existindo na BD con `baixa=True`.

- [ ] **Step 6: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir pestana de Tratamentos"
```

---

## Task 8: Pestana de Fertilización na UI

**Files:**
- Modify: `src/horta/ui/pages/horta_detalle.py`

**Interfaces:**
- Consumes: `horta.services.fertilizacions.{crear_fertilizacion, actualizar_fertilizacion, eliminar_fertilizacion, listar_fertilizacions}` (Task 4); `horta.ui.filtros.filtrar_filas`.

Mesmo patrón exacto que a Task 7 (Tratamentos), coa entidade Fertilización.

- [ ] **Step 1: Engadir os imports e cargar as fertilizacións**

Inserir despois do import de `errors` e antes do de `hortas` (orde alfabética: `animais`, `cultivos`, `errors`, `fertilizacions`, `hortas`, `parcelas`, `tratamentos`). O bloque `from horta.services.errors import PermisoDenegadoError` xa existe; engadir só o bloque novo xusto despois del, antes do xa existente `from horta.services.hortas import (...)`:

```python
from horta.services.fertilizacions import (
    actualizar_fertilizacion,
    crear_fertilizacion,
    eliminar_fertilizacion,
    listar_fertilizacions,
)
```

Dentro de `horta_detalle_page`, substituír:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        tratamentos = listar_tratamentos(session, actor, horta_id)
```

por:

```python
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        tratamentos = listar_tratamentos(session, actor, horta_id)
        fertilizacions = listar_fertilizacions(session, actor, horta_id)
```

- [ ] **Step 2: Engadir a pestana de Fertilización**

Substituír:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_tratamentos = ui.tab("Tratamentos")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_tratamentos):
            _seccion_tratamentos(horta_id, tratamentos, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

por:

```python
    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_cultivos = ui.tab("Cultivos")
        pestana_tratamentos = ui.tab("Tratamentos")
        pestana_fertilizacion = ui.tab("Fertilización")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_cultivos):
            _seccion_cultivos(horta_id, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_tratamentos):
            _seccion_tratamentos(horta_id, tratamentos, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_fertilizacion):
            _seccion_fertilizacion(horta_id, fertilizacions, cultivos, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)
```

- [ ] **Step 3: Engadir a función `_seccion_fertilizacion`**

Engadir esta función despois de `_seccion_tratamentos` remata e antes de `def _seccion_animais(...)`:

```python
def _seccion_fertilizacion(
    horta_id: int, fertilizacions: list, cultivos: list, parcelas: list, pode_editar: bool
) -> None:
    parcelas_por_id = {p.id: p.nome for p in parcelas}
    etiquetas_cultivo = {
        c.id: f"{c.especie} — {parcelas_por_id.get(c.parcela_id, '?')}" for c in cultivos
    }

    def _parsear_data(texto: str) -> Any:
        if not texto:
            raise ValueError("A data é obrigatoria")
        try:
            return date.fromisoformat(texto)
        except ValueError as erro:
            raise ValueError(f"Data non válida: {texto!r} (usa o formato AAAA-MM-DD)") from erro

    if pode_editar:
        with ui.dialog() as dialog_nova_fertilizacion, ui.card():
            ui.label("Nova fertilización").classes("text-md font-bold")
            cultivo_select = ui.select(etiquetas_cultivo, label="Cultivo")
            data_input = ui.input("Data (AAAA-MM-DD)")
            tipo_select = ui.select(
                ["emenda", "abonado_fondo", "cobertoira"], label="Tipo"
            )
            produto_input = ui.input("Produto")

            def crear() -> None:
                if not (
                    cultivo_select.value
                    and data_input.value
                    and tipo_select.value
                    and produto_input.value
                ):
                    ui.notify("Cultivo, data, tipo e produto son obrigatorios", type="negative")
                    return
                try:
                    data_valor = _parsear_data(data_input.value)
                except ValueError as erro:
                    ui.notify(str(erro), type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creada = executar_accion(
                        session,
                        lambda: crear_fertilizacion(
                            session,
                            actor_actual,
                            cultivo_select.value,
                            data_valor,
                            tipo_select.value,
                            produto_input.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_fertilizacion.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Fertilización").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Nova fertilización", icon="add", on_click=dialog_nova_fertilizacion.open)

    todas_as_filas = [
        {
            "id": f.id,
            "cultivo": etiquetas_cultivo.get(f.cultivo_id, "?"),
            "data": f.data.isoformat(),
            "tipo": f.tipo,
            "produto": f.produto,
        }
        for f in fertilizacions
    ]

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        tipo_filtro_select = ui.select(
            ["Todos", "emenda", "abonado_fondo", "cobertoira"], label="Tipo", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "cultivo", "label": "Cultivo", "field": "cultivo"},
                {"name": "data", "label": "Data", "field": "data"},
                {"name": "tipo", "label": "Tipo", "field": "tipo"},
                {"name": "produto", "label": "Produto", "field": "produto"},
            ],
            rows=todas_as_filas,
            row_key="id",
            selection="single" if pode_editar else None,
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        tipo_filtro = None if tipo_filtro_select.value == "Todos" else tipo_filtro_select.value
        taboa.rows = filtrar_filas(
            todas_as_filas,
            busca_input.value or "",
            ["cultivo", "data", "tipo", "produto"],
            {"tipo": tipo_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            if pode_editar:
                fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    tipo_filtro_select.on_value_change(refrescar_taboa)

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar a fertilización de «{taboa.selected[0]['produto']}»? "
                "Esta acción non se pode desfacer.",
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar fertilización").classes("text-md font-bold")
        data_edit = ui.input("Data (AAAA-MM-DD)")
        tipo_edit = ui.select(["emenda", "abonado_fondo", "cobertoira"], label="Tipo")
        produto_edit = ui.input("Produto")
        dose_edit = ui.input("Dose")
        superficie_edit = ui.number("Superficie (m²)")
        n_edit = ui.number("N (%)")
        p_edit = ui.number("P (%)")
        k_edit = ui.number("K (%)")
        carbono_organico_edit = ui.number("Carbono orgánico (%)")
        micronutrientes_edit = ui.input("Micronutrientes")
        asesoramento_edit = ui.input("Asesoramento recibido")
        notas_edit = ui.textarea("Notas")

        def gardar() -> None:
            if not taboa.selected:
                return
            fertilizacion_id = taboa.selected[0]["id"]
            if not (tipo_edit.value and produto_edit.value):
                ui.notify("Tipo e produto son obrigatorios", type="negative")
                return
            try:
                data_valor = _parsear_data(data_edit.value)
            except ValueError as erro:
                ui.notify(str(erro), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        f
                        for f in listar_fertilizacions(session, actor_actual, horta_id)
                        if f.id == fertilizacion_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Esa fertilización xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_fertilizacion(
                        session,
                        actor_actual,
                        obxectivo,
                        data=data_valor,
                        tipo=tipo_edit.value,
                        produto=produto_edit.value,
                        dose=dose_edit.value or None,
                        superficie=superficie_edit.value,
                        n=n_edit.value,
                        p=p_edit.value,
                        k=k_edit.value,
                        carbono_organico=carbono_organico_edit.value,
                        micronutrientes=micronutrientes_edit.value or None,
                        asesoramento_recibido=asesoramento_edit.value or None,
                        notas=notas_edit.value or None,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fertilizacion_id = taboa.selected[0]["id"]
        fertilizacion_completa = next(
            (f for f in fertilizacions if f.id == fertilizacion_id), None
        )
        if fertilizacion_completa is None:
            return
        data_edit.value = fertilizacion_completa.data.isoformat()
        tipo_edit.value = fertilizacion_completa.tipo
        produto_edit.value = fertilizacion_completa.produto
        dose_edit.value = fertilizacion_completa.dose or ""
        superficie_edit.value = fertilizacion_completa.superficie
        n_edit.value = fertilizacion_completa.n
        p_edit.value = fertilizacion_completa.p
        k_edit.value = fertilizacion_completa.k
        carbono_organico_edit.value = fertilizacion_completa.carbono_organico
        micronutrientes_edit.value = fertilizacion_completa.micronutrientes or ""
        asesoramento_edit.value = fertilizacion_completa.asesoramento_recibido or ""
        notas_edit.value = fertilizacion_completa.notas or ""
        dialog_editar.open()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        fertilizacion_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (
                    f
                    for f in listar_fertilizacions(session, actor_actual, horta_id)
                    if f.id == fertilizacion_id
                ),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa fertilización xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_fertilizacion(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()
```

- [ ] **Step 4: Executar a suite completa, ruff e mypy**

Run: `uv run pytest -v` → PASS sen regresións.
Run: `uv run ruff check src tests` → sen erros.
Run: `uv run mypy src` → sen erros.

- [ ] **Step 5: Verificación manual**

Mesmo procedemento que na Task 7, na pestana "Fertilización": crear, buscar, filtrar por Tipo, editar (engadir N/P/K), eliminar e comprobar a baixa lóxica na BD.

- [ ] **Step 6: Commit**

```bash
git add src/horta/ui/pages/horta_detalle.py
git commit -m "feat: engadir pestana de Fertilización"
```

---

## Task 9: Verificación final de conxunto

**Files:**
- Ningún ficheiro novo — só verificación.

- [ ] **Step 1: Executar toda a suite de tests**

Run: `uv run pytest -v`
Expected: todos os tests pasan (os existentes máis os novos das Tasks 1-5).

- [ ] **Step 2: Ruff e mypy**

Run: `uv run ruff check src tests` → sen erros.
Run: `uv run mypy src` → sen erros.

- [ ] **Step 3: Verificación manual de conxunto**

Run: `uv run python src/horta/main.py` (en segundo plano)

1. Fluxo completo: crear unha parcela → crear un cultivo nesa parcela → crear un tratamento e unha fertilización nese cultivo → editar cada un → confirmar que todo aparece correctamente nas súas pestanas respectivas.
2. Eliminar a parcela creada e confirmar (vía a UI, ou consultando a BD con `uv run python -c "..."`) que o cultivo, o tratamento e a fertilización desapareceron todos (borrado físico en cascada).
3. Confirmar que un usuario con rol lector nesa horta pode ver e buscar/filtrar as catro pestanas novas (Cultivos/Tratamentos/Fertilización engadidas, e as tres xa existentes), pero non ve os botóns de crear/editar/eliminar.
4. Confirmar que a suite completa e ruff/mypy seguen limpos tras a verificación manual (sen ficheiros esquecidos sen comitear).

Parar o servidor despois de verificar.

- [ ] **Step 4: Commit final (só se houbo que corrixir algo nos pasos 1-2)**

```bash
git add -A
git commit -m "chore: corrixir avisos tras a verificación final"
```

(Omitir este commit se non houbo cambios que facer.)
