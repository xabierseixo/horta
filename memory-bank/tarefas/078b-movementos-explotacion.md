# Tarefa 078b — Entradas e saídas de animais (3/11): conservar ao borrar a explotación

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 078. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Unha explotación con entradas e saídas de animais non se pode borrar; se só ten os movementos iniciais, bórranse cos grupos. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.maquina import Maquina
```

Despois:
```python
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
```

### Paso 2 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten coidados de animais rexistrados e debe conservarse "
            "(obriga legal)."
        )
```

Despois:
```python
            "Esta explotación ten coidados de animais rexistrados e debe conservarse "
            "(obriga legal)."
        )
    if session.query(MovementoAnimal).filter(
        MovementoAnimal.horta_id == horta.id, MovementoAnimal.tipo != "inicial"
    ).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten entradas e saídas de animais rexistradas e debe conservarse "
            "(obriga legal)."
        )
```

### Paso 3 — `src/horta/services/hortas.py`

Antes:
```python
        session.delete(parcela)
```

Despois:
```python
        session.delete(parcela)
    session.query(MovementoAnimal).filter_by(horta_id=horta.id).delete()
    session.flush()
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (3/11): conservar ao borrar a explotación: feito.
