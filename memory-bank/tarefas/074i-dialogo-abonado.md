# Tarefa 074i — Formularios separados (3/7): abonado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do abonado sepárase da súa páxina (dialogo_abonado). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/abonados.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from __future__ import annotations

```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/abonados.py`

Antes:
```python
from horta.ui.campos import campo_data
```

Despois:
```python
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
```

### Paso 3 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_fertilizacion")}
        metodos = {v.codigo: v.descricion
                   for v in valores_vixentes(session, "metodo_fertilizacion")}
        practicas = {v.codigo: v.descricion for v in valores_vixentes(session, "boas_practicas")
                     if "fertilizacion" in (v.categoria or "")}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

Despois:
```python
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
```

### Paso 4 — `src/horta/ui/pages/abonados.py`

Antes:
```python
    if not tipos or not practicas:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return
```

Despois:
```python
    abrir = dialogo_abonado(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        with get_session() as session:
            a = session.get(Abonado, taboa.selected[0]["id"])
            if a is not None:
                _ = a.boas_practicas
                abrir(a)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        abonado_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Abonado, abonado_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_abonado(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este abonado? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar abonado", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_abonado(horta_id: int) -> Callable[[Abonado | None], None]:
    """Constrúe o diálogo de apuntar ou editar un abonado e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_fertilizacion")}
        metodos = {v.codigo: v.descricion
                   for v in valores_vixentes(session, "metodo_fertilizacion")}
        practicas = {v.codigo: v.descricion for v in valores_vixentes(session, "boas_practicas")
                     if "fertilizacion" in (v.categoria or "")}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 5 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        titulo = ui.label("Apuntar abonado").classes("text-h6")
```

Despois:
```python
        titulo = ui.label("Apuntar abonado").classes("text-h6")
        if not tipos or not practicas:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
```

### Paso 6 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        with get_session() as session:
            a = session.get(Abonado, taboa.selected[0]["id"])
            if a is not None:
                _ = a.boas_practicas
                abrir(a)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        abonado_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Abonado, abonado_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_abonado(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este abonado? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar abonado", icon="add", on_click=lambda: abrir(None))
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

Formularios separados (3/7): abonado: feito.
