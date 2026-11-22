# Tarefa 080c — Pastoreo (4/11): non borrar grupos con pastoreo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Un grupo de animais con pastoreo apuntado non se borra. Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

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
from horta.services.pastoreos import ten_pastoreo
```

### Paso 2 — `src/horta/services/animais.py`

Antes:
```python
            or ten_producion(session, animal.id)):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados, entradas e saídas ou produción apuntados e debe conservarse "
            "(obriga legal). Se xa non ten animais, apunta a súa saída ou morte")
```

Despois:
```python
            or ten_producion(session, animal.id) or ten_pastoreo(session, animal.id)):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados, entradas e saídas, produción ou pastoreos apuntados e debe "
            "conservarse (obriga legal). Se xa non ten animais, apunta a súa saída ou morte")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (4/11): non borrar grupos con pastoreo: feito.
