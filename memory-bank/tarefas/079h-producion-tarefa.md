# Tarefa 079h — Produción dos animais (10/11): tarefa de produción

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079. **Axente**: qwen-66 (pequena).

## Obxectivo

Unha tarefa pode ser de produción dos animais e, ao facela, queda ligada á produción apuntada. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.producion_animal import ProducionAnimal
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
    "movemento_animal": (MovementoAnimal, "data"),
```

Despois:
```python
    "movemento_animal": (MovementoAnimal, "data"),
    "producion_animal": (ProducionAnimal, "data"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (10/11): tarefa de produción: feito.
