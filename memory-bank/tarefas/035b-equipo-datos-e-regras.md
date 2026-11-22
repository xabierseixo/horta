# Tarefa 035b — Equipo: datos e regras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 035.

## Obxectivo

Base de Equipo segundo `docs/superpowers/specs/2026-10-23-equipo-design.md`: campos novos de `persoa` (conta, funcións, contacto, vínculo, horas/ano, formación, colectivo), migración que mete os membros actuais no equipo, servizo `equipo.py` (dar e quitar acceso, UTA) e o creador dunha explotación entra no equipo. Sen cambios na pantalla (tarefa 036).

## Ficheiros a tocar

- `src/horta/models/persoa.py`
- `alembic/versions/a7d2e5f8c3b1_equipo.py` (**ficheiro novo**)
- `src/horta/services/persoas.py`
- `src/horta/services/equipo.py` (**ficheiro novo**)
- `src/horta/services/hortas.py`
- `tests/services/test_equipo.py` (**ficheiro novo**)
- `tests/services/test_persoas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/equipo.py`

Contido completo:

```python
"""Equipo da explotación: persoas, as súas funcións e o seu acceso á app.

O acceso gárdase en HortaMembro (fronteira de seguridade); a persoa liga coa súa conta
por usuario_id. Deseño: docs/superpowers/specs/2026-10-23-equipo-design.md
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.auth import normalizar_email
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import (
    cambiar_rol_membro,
    comprobar_rol_horta,
    engadir_membro,
    quitar_membro,
)

HORAS_UTA = 1920
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def acceso_da_persoa(session: Session, persoa: Persoa) -> RolHorta | None:
    if persoa.usuario_id is None:
        return None
    membro = session.get(HortaMembro, (persoa.horta_id, persoa.usuario_id))
    return membro.rol if membro else None


def conceder_acceso(
    session: Session, actor: Usuario, persoa: Persoa, email: str, rol: RolHorta
) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    usuario = session.query(Usuario).filter_by(email=normalizar_email(email)).one_or_none()
    if usuario is None:
        raise OperacionNonPermitidaError(
            "Non hai ningunha conta con ese email. Pídelle ao administrador que a cree."
        )
    outra = (
        session.query(Persoa)
        .filter(Persoa.horta_id == persoa.horta_id, Persoa.usuario_id == usuario.id,
                Persoa.id != persoa.id)
        .first()
    )
    if outra is not None:
        raise OperacionNonPermitidaError(f"Esa conta xa está ligada a {outra.nome}")
    if session.get(HortaMembro, (persoa.horta_id, usuario.id)) is None:
        engadir_membro(session, actor, persoa.horta_id, usuario, rol)
    else:
        cambiar_rol_membro(session, actor, persoa.horta_id, usuario.id, rol)
    persoa.usuario_id = usuario.id
    session.commit()


def retirar_acceso(session: Session, actor: Usuario, persoa: Persoa) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    if persoa.usuario_id is None:
        return
    quitar_membro(session, actor, persoa.horta_id, persoa.usuario_id)
    persoa.usuario_id = None
    session.commit()


def uta_equipo(session: Session, actor: Usuario, horta_id: int) -> float:
    """Unidades de traballo agrario: horas ao ano das persoas activas / 1.920."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    horas = sum(
        p.horas_ano or 0
        for p in session.query(Persoa).filter_by(horta_id=horta_id, activa=True)
    )
    return round(horas / HORAS_UTA, 2)
```

### Paso 2 — `src/horta/services/hortas.py`: o creador entra no equipo

Antes:
```python
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.commit()
    return horta
```

Despois:
```python
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.add(Persoa(horta_id=horta.id, nome=actor.nome, usuario_id=actor.id,
                       email=actor.email))
    session.commit()
    return horta
```

### Paso 3 — crear o ficheiro `tests/services/test_equipo.py`

Contido completo:

```python
from datetime import date

import pytest

from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.equipo import acceso_da_persoa, conceder_acceso, retirar_acceso, uta_equipo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.persoas import actualizar_persoa, crear_persoa


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


def test_o_creador_entra_no_equipo_ligado_a_sua_conta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    assert persoa.usuario_id == ana.id
    assert acceso_da_persoa(session, persoa) == RolHorta.ADMIN


def test_conceder_e_retirar_acceso(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Bea")
    conceder_acceso(session, ana, xan, " Bea@Example.com", RolHorta.EDITOR)
    assert acceso_da_persoa(session, xan) == RolHorta.EDITOR
    conceder_acceso(session, ana, xan, "bea@example.com", RolHorta.LECTOR)
    assert acceso_da_persoa(session, xan) == RolHorta.LECTOR
    retirar_acceso(session, ana, xan)
    assert xan.usuario_id is None
    assert session.get(HortaMembro, (horta.id, bea.id)) is None


def test_email_sen_conta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Xan")
    with pytest.raises(OperacionNonPermitidaError, match="Non hai ningunha conta"):
        conceder_acceso(session, ana, xan, "ninguen@example.com", RolHorta.LECTOR)


def test_unha_conta_non_pode_ir_a_duas_persoas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Xan")
    with pytest.raises(OperacionNonPermitidaError, match="xa está ligada"):
        conceder_acceso(session, ana, xan, "ana@example.com", RolHorta.ADMIN)


def test_non_se_pode_retirar_o_ultimo_admin(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="polo menos un administrador"):
        retirar_acceso(session, ana, persoa)


def test_uta_do_equipo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    actualizar_persoa(session, ana, persoa, horas_ano=1920.0, vinculo="titular")
    crear_persoa(session, ana, horta.id, "Xan", horas_ano=960.0, vinculo="asalariado")
    assert uta_equipo(session, ana, horta.id) == 1.5


@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"vinculo": "veciño"}, "Vínculo non válido"),
        ({"horas_ano": 5000.0}, "horas ao ano"),
        ({"xenero": "x"}, "Xénero non válido"),
        ({"data_nacemento": date(2030, 1, 1)}, "data de nacemento"),
    ],
)
def test_validacions_do_equipo(session, campos, mensaxe):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_persoa(session, ana, horta.id, "Xan", **campos)
```

### Paso 4 — `tests/services/test_persoas.py`: o creador xa está no equipo

Antes:
```python
    assert [p.nome for p in listar_persoas(session, ana, horta.id)] == ["Xan"]
```

Despois:
```python
    assert "Xan" in [p.nome for p in listar_persoas(session, ana, horta.id)]
```

### Paso 5 — mesmo ficheiro

Antes:
```python
    assert listar_persoas(session, ana, horta.id) == []
    assert len(listar_persoas(session, ana, horta.id, so_activas=False)) == 1
```

Despois:
```python
    assert [p.nome for p in listar_persoas(session, ana, horta.id)] == ["ana"]
    assert len(listar_persoas(session, ana, horta.id, so_activas=False)) == 2
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
