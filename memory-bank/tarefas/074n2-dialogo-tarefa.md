# Tarefa 074n2 — Formularios separados: nova tarefa

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074n. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A sección Tarefas usa o formulario de nova tarefa de ui/dialogo_tarefa.py. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
    contar_tarefas_pendentes,
    crear_tarefa,
```

Despois:
```python
    contar_tarefas_pendentes,
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.dialogo_datos_caderno import boton_datos_caderno
```

Despois:
```python
from horta.ui.dialogo_datos_caderno import boton_datos_caderno
from horta.ui.dialogo_tarefa import PRIORIDADES_TAREFA, dialogo_nova_tarefa
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")

_PRIORIDADES_TAREFA = ("baixa", "media", "alta")
```

Despois:
```python
_UNIDADES_CULTIVO = ("kg", "unidades", "ducias", "mazos")

```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        with ui.dialog() as dialog_nova_tarefa, ui.card():
            ui.label("Nova tarefa").classes("text-md font-bold")
            descricion_input = ui.input("Descrición")
            parcela_select = ui.select(opcions_parcela, label="Parcela", value="")
            cultivo_select = ui.select(opcions_cultivo, label="Cultivo", value="")
            data_input = campo_data("Data (opcional)")
            prioridade_select = ui.select(
                list(_PRIORIDADES_TAREFA), label="Prioridade", value="media"
            )

            def crear() -> None:
                if not descricion_input.value:
                    ui.notify("A descrición é obrigatoria", type="negative")
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
                        lambda: crear_tarefa(
                            session,
                            actor_actual,
                            horta_id,
                            descricion_input.value,
                            parcela_id=parcela_select.value or None,
                            cultivo_id=cultivo_select.value or None,
                            data=data_valor,
                            prioridade=prioridade_select.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_tarefa.close).props("flat")
```

Despois:
```python
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
            ui.button("Nova tarefa", icon="add", on_click=dialog_nova_tarefa.open)
```

Despois:
```python
            ui.button("Nova tarefa", icon="add", on_click=abrir_nova_tarefa)
```

### Paso 6 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        prioridade_edit = ui.select(list(_PRIORIDADES_TAREFA), label="Prioridade")
```

Despois:
```python
        prioridade_edit = ui.select(list(PRIORIDADES_TAREFA), label="Prioridade")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios separados: nova tarefa: feito.
