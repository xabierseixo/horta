# Tarefa 076c — Tarefas por facer (4/16): pezas da pantalla

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» propón quen ía facer a tarefa (só persoas activas); diálogo para dar por feita unha tarefa sen tipo e axuda para ligar a tarefa ao traballo gardado. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/quen.py`
- `src/horta/ui/facer_tarefa.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/quen.py`

Antes:
```python
from horta.services.diario import ultima_persoa
from horta.ui.sesion import usuario_actual


def proposta_quen(horta_id: int) -> int | None:
    """Quen fixo o último traballo, para propoñelo ao apuntar o seguinte."""
    with get_session() as session:
        actor = usuario_actual(session)
        return ultima_persoa(session, actor, horta_id) if actor else None
```

Despois:
```python
from horta.models.persoa import Persoa
from horta.models.tarefa import Tarefa
from horta.services.diario import ultima_persoa
from horta.ui.sesion import usuario_actual


def proposta_quen(horta_id: int, tarefa: Tarefa | None = None) -> int | None:
    """Quen ía facer a tarefa ou, se non, quen fixo o último traballo, para propoñelo (só se
    segue activa no equipo: os formularios só ofrecen as persoas activas)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return None
        persoa_id = (tarefa.persoa_id if tarefa is not None and tarefa.persoa_id is not None
                     else ultima_persoa(session, actor, horta_id))
        persoa = session.get(Persoa, persoa_id) if persoa_id is not None else None
        return persoa.id if persoa is not None and persoa.activa else None
```

### Paso 2 — crear o ficheiro `src/horta/ui/facer_tarefa.py`

Contido completo:
```python
"""Facer unha tarefa (un traballo por facer): con tipo, no formulario dese tipo xa enchido;
sen tipo, dicindo quen a fixo, cando e cantas horas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui
from sqlalchemy.orm import Session

from horta.db import Base, get_session
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.persoas import listar_persoas
from horta.services.tarefas import facer_tarefa, marcar_feita
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual


def rematar_tarefa(
    session: Session, actor: Usuario, tarefa_id: int | None, rexistro: Base
) -> None:
    """Despois de apuntar o traballo dunha tarefa, déixaa feita e ligada a el."""
    tarefa = session.get(Tarefa, tarefa_id) if tarefa_id else None
    if tarefa is not None:
        facer_tarefa(session, actor, tarefa, rexistro)


def dialogo_tarefa_feita(horta_id: int) -> Callable[[Tarefa], None]:
    """Diálogo para dar por feita unha tarefa sen tipo; devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    tarefa_id: dict[str, int | None] = {"id": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        titulo = ui.label("").classes("text-h6")
        quen = ui.select(persoas, label="Quen o fixo").classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        horas = ui.input("Horas de traballo").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                tarefa = session.get(Tarefa, tarefa_id["id"])
                if tarefa is None:
                    ui.notify("Esa tarefa xa non existe", type="negative")
                    return
                ok = executar_accion(session, lambda: marcar_feita(
                    session, actor_actual, tarefa, quen.value, parsear_data(data.value),
                    parsear_decimal(horas.value)))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Feita", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(tarefa: Tarefa) -> None:
        tarefa_id["id"] = tarefa.id
        titulo.text = tarefa.descricion
        quen.value = proposta_quen(horta_id, tarefa)
        data.value = date.today().isoformat()
        horas.value = ""
        dialogo.open()

    return abrir
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (4/16): pezas da pantalla: feito.
