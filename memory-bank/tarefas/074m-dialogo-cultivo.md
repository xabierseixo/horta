# Tarefa 074m — Formularios separados (7/7): cultivo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do cultivo (tamén a súa sementeira ou plantación) sepárase da súa páxina (dialogo_cultivo). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from collections import defaultdict
```

Despois:
```python
from collections import defaultdict
from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
        opcions_cultivo = {c.codigo: nome for c, nome in buscar_cultivos(session, "", 2000)}
        opcions = {
            campo: {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}
            for campo, catalogo in _CATALOGOS.items()
        }
```

Despois:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
```

### Paso 3 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
    if not pode_editar:
        return
```

Despois:
```python
    if not pode_editar:
        return

    abrir = dialogo_cultivo(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un cultivo na táboa", type="warning")
            return
        abrir(next(x for x in cultivos if x.id == taboa.selected[0]["id"]))

    def eliminar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un cultivo na táboa", type="warning")
            return
        cultivo_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                cultivo = session.get(Cultivo, cultivo_id)
                if actor is None or cultivo is None:
                    return
                ok = executar_accion(session, lambda: eliminar_cultivo(session, actor, cultivo))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion("Eliminar este cultivo?", confirmar)

    with ui.row():
        ui.button("Novo cultivo", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Eliminar", icon="delete", on_click=eliminar).props("outline color=negative")


def dialogo_cultivo(horta_id: int) -> Callable[[Cultivo | None], None]:
    """Constrúe o diálogo de crear ou editar un cultivo (tamén a súa sementeira ou plantación)
    e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        cultivos = listar_cultivos(session, actor, horta_id)
        parcelas = listar_parcelas(session, actor, horta_id)
        opcions_cultivo = {c.codigo: nome for c, nome in buscar_cultivos(session, "", 2000)}
        opcions = {
            campo: {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}
            for campo, catalogo in _CATALOGOS.items()
        }
    nome_parcela = {p.id: p.nome for p in parcelas}
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
    def abrir_novo() -> None:
        editando["id"] = None
        titulo.text = "Novo cultivo"
        parcela.value = cultivo_oficial.value = None
        for campo in campos_texto:
            campo.value = ""
        for selector in campos_select:
            selector.value = None
        superficie.establecer(None)
        tipo_inicio.value = "sementeira"
        sistema.value = _POR_DEFECTO["sistema_cultivo"]
        destino.value = _POR_DEFECTO["destino"]
        eco.value = _POR_DEFECTO["certificacion_ecoloxica"]
        integrada.value = False
        for casilla in casillas:
            casilla.value = False
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un cultivo na táboa", type="warning")
            return
        c = next(x for x in cultivos if x.id == taboa.selected[0]["id"])
```

Despois:
```python
    def abrir(c: Cultivo | None) -> None:
        if c is None:
            editando["id"] = None
            titulo.text = "Novo cultivo"
            parcela.value = cultivo_oficial.value = None
            for campo in campos_texto:
                campo.value = ""
            for selector in campos_select:
                selector.value = None
            superficie.establecer(None)
            tipo_inicio.value = "sementeira"
            sistema.value = _POR_DEFECTO["sistema_cultivo"]
            destino.value = _POR_DEFECTO["destino"]
            eco.value = _POR_DEFECTO["certificacion_ecoloxica"]
            integrada.value = False
            for casilla in casillas:
                casilla.value = False
            dialogo.open()
            return
```

### Paso 5 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
    def eliminar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un cultivo na táboa", type="warning")
            return
        cultivo_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                cultivo = session.get(Cultivo, cultivo_id)
                if actor is None or cultivo is None:
                    return
                ok = executar_accion(session, lambda: eliminar_cultivo(session, actor, cultivo))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion("Eliminar este cultivo?", confirmar)

    with ui.row():
        ui.button("Novo cultivo", icon="add", on_click=abrir_novo)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")
        ui.button("Eliminar", icon="delete", on_click=eliminar).props("outline color=negative")
```

Despois:
```python
    return abrir
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios separados (7/7): cultivo: feito.
