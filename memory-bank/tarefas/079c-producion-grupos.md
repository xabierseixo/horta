# Tarefa 079c — Produción dos animais (4/11): non borrar grupos con produción

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Un grupo de animais con produción apuntada non se borra. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/services/animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/animais.py`

Antes:
```python
    ten_movementos,
)
```

Despois:
```python
    ten_movementos,
)
from horta.services.producions_animais import ten_producion
```

### Paso 2 — `src/horta/services/animais.py`

Antes:
```python
    if ten_coidados(session, animal.id) or ten_movementos(session, animal.id):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados ou entradas e saídas apuntados e debe conservarse "
```

Despois:
```python
    if (ten_coidados(session, animal.id) or ten_movementos(session, animal.id)
            or ten_producion(session, animal.id)):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados, entradas e saídas ou produción apuntados e debe conservarse "
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (4/11): non borrar grupos con produción: feito.
