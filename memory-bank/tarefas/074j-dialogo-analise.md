# Tarefa 074j — Formularios separados (4/7): toma de mostras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario da análise sepárase da súa páxina (dialogo_analise). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/analises.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/analises.py`

Antes:
```python
from __future__ import annotations

```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/analises.py`

Antes:
```python
from horta.ui.campos import campo_data
```

Despois:
```python
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
```

### Paso 3 — `src/horta/ui/pages/analises.py`

Antes:
```python
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
        substancias = {v.codigo: v.descricion
                       for v in valores_vixentes(session, "substancia_activa")}
```

Despois:
```python
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
```

### Paso 4 — `src/horta/ui/pages/analises.py`

Antes:
```python
    if not materiais:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return
```

Despois:
```python
    abrir = dialogo_analise(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        abrir(next(a for a in analises if a.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        analise_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Analise, analise_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_analise(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta análise? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar análise", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_analise(horta_id: int) -> Callable[[Analise | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha análise e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
        substancias = {v.codigo: v.descricion
                       for v in valores_vixentes(session, "substancia_activa")}
```

### Paso 5 — `src/horta/ui/pages/analises.py`

Antes:
```python
        titulo = ui.label("Apuntar análise").classes("text-h6")
```

Despois:
```python
        titulo = ui.label("Apuntar análise").classes("text-h6")
        if not materiais:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
```

### Paso 6 — `src/horta/ui/pages/analises.py`

Antes:
```python
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        abrir(next(a for a in analises if a.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        analise_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Analise, analise_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_analise(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta análise? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar análise", icon="add", on_click=lambda: abrir(None))
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

Formularios separados (4/7): toma de mostras: feito.
