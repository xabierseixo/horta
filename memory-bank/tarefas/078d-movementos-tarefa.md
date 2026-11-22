# Tarefa 078d — Entradas e saídas de animais (5/11): tarefa de entrada ou saída

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 078a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Unha tarefa pode ser unha entrada ou saída de animais e, ao facela, queda ligada ao movemento apuntado. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/tarefas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/tarefas.py`

Antes:
```python
from horta.models.labor import Labor
```

Despois:
```python
from horta.models.labor import Labor
from horta.models.movemento_animal import MovementoAnimal
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
    "coidado_animal": (CoidadoAnimal, "data_inicio"),
```

Despois:
```python
    "coidado_animal": (CoidadoAnimal, "data_inicio"),
    "movemento_animal": (MovementoAnimal, "data"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (5/11): tarefa de entrada ou saída: feito.
