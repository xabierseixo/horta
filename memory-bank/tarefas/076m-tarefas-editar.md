# Tarefa 076m — Tarefas por facer (14/16): editar tipo e quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 076l. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

En Tarefas, editar unha tarefa permite cambiar que traballo é e quen o vai facer. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.dialogo_tarefa import PRIORIDADES_TAREFA, dialogo_nova_tarefa
```

Despois:
```python
from horta.ui.dialogo_tarefa import PRIORIDADES_TAREFA, dialogo_nova_tarefa, opcions_tarefa
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
```

Despois:
```python
        abrir_nova_tarefa = dialogo_nova_tarefa(horta_id)
        with get_session() as session:
            actor = usuario_actual(session)
            opcions_tipo, opcions_persoa = (
                opcions_tarefa(session, actor, horta_id) if actor else ({}, {}))
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        descricion_edit = ui.input("Descrición")
```

Despois:
```python
        descricion_edit = ui.input("Descrición")
        tipo_edit = ui.select(opcions_tipo, label="Que traballo é")
        persoa_edit = ui.select(opcions_persoa, label="Quen o vai facer")
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                        descricion=descricion_edit.value,
```

Despois:
```python
                        descricion=descricion_edit.value,
                        tipo=tipo_edit.value or None,
                        persoa_id=persoa_edit.value or None,
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        descricion_edit.value = tarefa_completa.descricion
```

Despois:
```python
        descricion_edit.value = tarefa_completa.descricion
        tipo_edit.value = tarefa_completa.tipo or ""
        persoa_edit.value = (tarefa_completa.persoa_id
                             if tarefa_completa.persoa_id in opcions_persoa else "")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (14/16): editar tipo e quen: feito.
