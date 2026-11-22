# Tarefa 077i — Coidado dos animais (10/10): editar a tarefa

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 077g e 077h. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

En Tarefas, editar unha tarefa permite escoller o grupo de animais. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.dialogo_tarefa import PRIORIDADES_TAREFA, dialogo_nova_tarefa, opcions_tarefa
```

Despois:
```python
from horta.ui.dialogo_tarefa import (
    PRIORIDADES_TAREFA,
    dialogo_nova_tarefa,
    opcions_animais,
    opcions_tarefa,
)
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                opcions_tarefa(session, actor, horta_id) if actor else ({}, {}))
```

Despois:
```python
                opcions_tarefa(session, actor, horta_id) if actor else ({}, {}))
            opcions_animal = opcions_animais(session, actor, horta_id) if actor else {}
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        cultivo_edit = ui.select(opcions_cultivo, label="Cultivo")
```

Despois:
```python
        cultivo_edit = ui.select(opcions_cultivo, label="Cultivo")
        animal_edit = ui.select(opcions_animal, label="Animais")
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                        cultivo_id=cultivo_edit.value or None,
```

Despois:
```python
                        cultivo_id=cultivo_edit.value or None,
                        animal_id=animal_edit.value or None,
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        cultivo_edit.value = tarefa_completa.cultivo_id or ""
```

Despois:
```python
        cultivo_edit.value = tarefa_completa.cultivo_id or ""
        animal_edit.value = (tarefa_completa.animal_id
                             if tarefa_completa.animal_id in opcions_animal else "")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (10/10): editar a tarefa: feito.
