# Tarefa 080b — Pastoreo (3/11): conservar cultivos e parcelas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 080. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Un cultivo ou unha parcela con pastoreo non se borra. Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `src/horta/services/parcelas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
```

### Paso 2 — `src/horta/services/cultivos.py`

Antes:
```python
            "Podes marcalo como rematado."
        )
```

Despois:
```python
            "Podes marcalo como rematado."
        )
    if session.query(PastoreoLeira).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten pastoreos rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
```

### Paso 3 — `src/horta/services/parcelas.py`

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.pastoreo import PastoreoLeira
```

### Paso 4 — `src/horta/services/parcelas.py`

Antes:
```python
            "Esta parcela ten labores rexistrados e debe conservarse (obriga legal)."
        )
```

Despois:
```python
            "Esta parcela ten labores rexistrados e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(PastoreoLeira).filter(
        PastoreoLeira.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten pastoreos rexistrados e debe conservarse (obriga legal)."
        )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (3/11): conservar cultivos e parcelas: feito.
