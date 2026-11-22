# Tarefa 074h — Formularios separados (2/7): labor

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do labor sepárase da súa páxina (dialogo_labor). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/labores.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/labores.py`

Antes:
```python
from __future__ import annotations

```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.ui.campos import campo_data
```

Despois:
```python
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
```

### Paso 3 — `src/horta/ui/pages/labores.py`

Antes:
```python
        coberturas = {v.codigo: v.descricion
                      for v in valores_vixentes(session, "tipo_cobertura_solo")}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 4 — `src/horta/ui/pages/labores.py`

Antes:
```python
    if not tipos:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return
```

Despois:
```python
    abrir = dialogo_labor(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        with get_session() as session:
            lab = session.get(Labor, taboa.selected[0]["id"])
            if lab is not None:
                abrir(lab)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        labor_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                lab = session.get(Labor, labor_id)
                if actor_actual is None or lab is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_labor(
                    session, actor_actual, lab))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este labor? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar labor", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_labor(horta_id: int) -> Callable[[Labor | None], None]:
    """Constrúe o diálogo de apuntar ou editar un labor e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_labor")}
        coberturas = {v.codigo: v.descricion
                      for v in valores_vixentes(session, "tipo_cobertura_solo")}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

### Paso 5 — `src/horta/ui/pages/labores.py`

Antes:
```python
        titulo = ui.label("Apuntar labor").classes("text-h6")
```

Despois:
```python
        titulo = ui.label("Apuntar labor").classes("text-h6")
        if not tipos:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
```

### Paso 6 — `src/horta/ui/pages/labores.py`

Antes:
```python
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        with get_session() as session:
            lab = session.get(Labor, taboa.selected[0]["id"])
            if lab is not None:
                abrir(lab)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        labor_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                lab = session.get(Labor, labor_id)
                if actor_actual is None or lab is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_labor(
                    session, actor_actual, lab))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este labor? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar labor", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")
```

Despois:
```python
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

Formularios separados (2/7): labor: feito.
