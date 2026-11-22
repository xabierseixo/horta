# Tarefa 074k — Formularios separados (5/7): tratamento de instalacións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O formulario do tratamento de instalacións sepárase da súa páxina (dialogo_tratamento_instalacion). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from __future__ import annotations

```

Despois:
```python
from __future__ import annotations

from collections.abc import Callable
```

### Paso 2 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        tratamentos = listar_tratamentos_instalacion(session, actor, horta_id)
        problemas = {t: {v.codigo: v.descricion for v in valores_vixentes(session, t)}
                     for t in TIPOS_PROBLEMA}
        xustificacions = {v.codigo: v.descricion
                          for v in valores_vixentes(session, "xustificacion")}
        tipos_produto = {v.codigo: v.descricion
                         for v in valores_vixentes(session, "tipo_produto")}
        unidades = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
```

Despois:
```python
        tratamentos = listar_tratamentos_instalacion(session, actor, horta_id)
```

### Paso 3 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
    if not pode_editar:
        return
```

Despois:
```python
    if not pode_editar:
        return

    abrir = dialogo_tratamento_instalacion(horta_id)

    def escollido() -> TratamentoInstalacion | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un tratamento na táboa", type="warning")
            return None
        return next(t for t in tratamentos if t.id == taboa.selected[0]["id"])

    def editar() -> None:
        t = escollido()
        if t is not None:
            abrir(t)

    def dar_de_baixa() -> None:
        t = escollido()
        if t is None:
            return
        tratamento_id = t.id

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                x = session.get(TratamentoInstalacion, tratamento_id)
                if actor_actual is None or x is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_tratamento_instalacion(
                    session, actor_actual, x))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este tratamento? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar postcolleita, almacén ou transporte", icon="add",
                  on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_tratamento_instalacion(
    horta_id: int,
) -> Callable[[TratamentoInstalacion | None], None]:
    """Constrúe o diálogo do tratamento de instalacións e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        problemas = {t: {v.codigo: v.descricion for v in valores_vixentes(session, t)}
                     for t in TIPOS_PROBLEMA}
        xustificacions = {v.codigo: v.descricion
                          for v in valores_vixentes(session, "xustificacion")}
        tipos_produto = {v.codigo: v.descricion
                         for v in valores_vixentes(session, "tipo_produto")}
        unidades = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
```

### Paso 4 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        dialogo.open()

    def escollido() -> TratamentoInstalacion | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un tratamento na táboa", type="warning")
            return None
        return next(t for t in tratamentos if t.id == taboa.selected[0]["id"])

    def editar() -> None:
        t = escollido()
        if t is not None:
            abrir(t)

    def dar_de_baixa() -> None:
        t = escollido()
        if t is None:
            return
        tratamento_id = t.id

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                x = session.get(TratamentoInstalacion, tratamento_id)
                if actor_actual is None or x is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_tratamento_instalacion(
                    session, actor_actual, x))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este tratamento? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar postcolleita, almacén ou transporte", icon="add",
                  on_click=lambda: abrir(None))
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

Formularios separados (5/7): tratamento de instalacións: feito.
