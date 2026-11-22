# Tarefa 080h — Pastoreo (10/11): tarefa de pastoreo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080. **Axente**: qwen-66 (pequena).

## Obxectivo

Unha tarefa pode ser de pastoreo e, ao facela, queda ligada ao pastoreo apuntado. Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

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
from horta.models.pastoreo import Pastoreo
```

### Paso 2 — `src/horta/services/tarefas.py`

Antes:
```python
    "producion_animal": (ProducionAnimal, "data"),
```

Despois:
```python
    "producion_animal": (ProducionAnimal, "data"),
    "pastoreo": (Pastoreo, "data_inicio"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (10/11): tarefa de pastoreo: feito.
