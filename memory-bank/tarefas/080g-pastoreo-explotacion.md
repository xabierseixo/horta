# Tarefa 080g — Pastoreo (9/11): conservar a explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080. **Axente**: qwen-66 (pequena).

## Obxectivo

Unha explotación con pastoreo non se pode borrar. Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

## Ficheiros a tocar

- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.pastoreo import Pastoreo
```

### Paso 2 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten produción dos animais rexistrada e debe conservarse."
        )
```

Despois:
```python
            "Esta explotación ten produción dos animais rexistrada e debe conservarse."
        )
    if session.query(Pastoreo).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten pastoreos rexistrados e debe conservarse (obriga legal)."
        )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (9/11): conservar a explotación: feito.
