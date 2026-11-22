# Tarefa 020 — Lista "para estar en regra" (servizo)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 018.

## Obxectivo

Función que di que lle falta a unha explotación profesional para estar en regra. As non profesionais devolven unha lista baleira.

## Ficheiros a tocar

- `src/horta/services/en_regra.py` (**ficheiro novo**)
- `tests/services/test_en_regra.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

### Paso 1 — crear o ficheiro `src/horta/services/en_regra.py`

Contido completo:

```python
"""Que lle falta a unha explotación profesional para estar en regra."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import Horta, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import ropo_vixente

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass(frozen=True)
class Requisito:
    texto: str
    cumprido: bool
    axuda: str


def requisitos_en_regra(
    session: Session, actor: Usuario, horta: Horta, hoxe: date | None = None
) -> list[Requisito]:
    comprobar_rol_horta(session, horta.id, actor, _ROLES_LECTURA)
    if not horta.uso_profesional:
        return []
    hoxe = hoxe or date.today()
    aplicadores = [
        p
        for p in session.query(Persoa).filter_by(horta_id=horta.id, activa=True, e_aplicador=True)
        if ropo_vixente(p, hoxe)
    ]
    ten_animais = session.query(Animal).filter_by(horta_id=horta.id).first() is not None
    requisitos = [
        Requisito(
            "NIF do titular",
            bool(horta.titular_nif),
            "Indícao en «Configurar explotación».",
        ),
        Requisito(
            "Inscrición no REAGA",
            bool(horta.codigo_reaga),
            "Solicítase na Oficina Agraria Comarcal ou na sede electrónica da Xunta.",
        ),
        Requisito(
            "Aplicador con carné ROPO en vigor",
            bool(aplicadores),
            "Dáo de alta na sección «Persoas».",
        ),
    ]
    if ten_animais:
        requisitos.append(
            Requisito(
                "Código REGA do gando",
                bool(horta.codigo_rega),
                "Solicítase na Oficina Agraria Comarcal.",
            )
        )
    return requisitos
```

### Paso 2 — crear o ficheiro `tests/services/test_en_regra.py`

Contido completo:

```python
from datetime import date

from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal
from horta.services.en_regra import requisitos_en_regra
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.persoas import crear_persoa


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


def test_non_profesional_non_ten_requisitos(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    assert requisitos_en_regra(session, ana, horta) == []


def test_profesional_sen_datos_ten_tres_pendentes(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    requisitos = requisitos_en_regra(session, ana, horta)
    assert [r.texto for r in requisitos] == [
        "NIF do titular",
        "Inscrición no REAGA",
        "Aplicador con carné ROPO en vigor",
    ]
    assert not any(r.cumprido for r in requisitos)


def test_profesional_completo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    actualizar_horta(
        session, ana, horta, titular_nif="12345678Z", codigo_reaga="ES150010000001"
    )
    crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
                 ropo_caducidade=date(2030, 1, 1))
    requisitos = requisitos_en_regra(session, ana, horta, hoxe=date(2026, 10, 22))
    assert all(r.cumprido for r in requisitos)


def test_con_animais_pide_rega(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación", uso_profesional=True)
    crear_animal(session, ana, horta.id, "galiñas", date(2026, 1, 1), cantidade=10)
    textos = [r.texto for r in requisitos_en_regra(session, ana, horta)]
    assert "Código REGA do gando" in textos
```

## Criterios de aceptación

- Non profesional → lista baleira; profesional → NIF, REAGA, aplicador con ROPO vixente e, se hai animais, REGA.
- Os catro tests novos pasan e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
