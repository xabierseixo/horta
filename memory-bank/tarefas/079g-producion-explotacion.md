# Tarefa 079g — Produción dos animais (9/11): conservar a explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079. **Axente**: qwen-66 (pequena).

## Obxectivo

Unha explotación con produción dos animais non se pode borrar. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.persoa import Persoa
```

Despois:
```python
from horta.models.persoa import Persoa
from horta.models.producion_animal import ProducionAnimal
```

### Paso 2 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten entradas e saídas de animais rexistradas e debe conservarse "
            "(obriga legal)."
        )
```

Despois:
```python
            "Esta explotación ten entradas e saídas de animais rexistradas e debe conservarse "
            "(obriga legal)."
        )
    if session.query(ProducionAnimal).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten produción dos animais rexistrada e debe conservarse."
        )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (9/11): conservar a explotación: feito.
