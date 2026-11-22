# Tarefa 075o — Formularios con quen (3/8): tratamento en instalacións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» e horas no formulario do tratamento en instalacións. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import listar_persoas
```

### Paso 2 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 3 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python

    editando: dict[str, int | None] = {"id": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar tratamento").classes("text-h6")
        tipo = ui.select(TIPOS_INSTALACION, value="postcolleita", label="Que tipo").classes(
            "w-full")
        data = campo_data("Data", date.today().isoformat())
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar tratamento").classes("text-h6")
        tipo = ui.select(TIPOS_INSTALACION, value="postcolleita", label="Que tipo").classes(
            "w-full")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
```

### Paso 4 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
            unidade = ui.select(unidades, label="Unidade", with_input=True).classes("col")
```

Despois:
```python
            unidade = ui.select(unidades, label="Unidade", with_input=True).classes("col")
        horas = ui.input("Horas de traballo").classes("w-full")
```

### Paso 5 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
                        unidade=unidade.value, notas=notas.value or None)
```

Despois:
```python
                        unidade=unidade.value, notas=notas.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value))
```

### Paso 6 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        data.value = (t.data if t else date.today()).isoformat()
```

Despois:
```python
        data.value = (t.data if t else date.today()).isoformat()
        persoa.value = (t.persoa_id if t.persoa_id in persoas else None) if t else (
            proposta_quen(horta_id))
        horas.value = f"{t.horas:g}" if t and t.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (3/8): tratamento en instalacións: feito.
