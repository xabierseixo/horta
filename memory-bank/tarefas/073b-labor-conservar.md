# Tarefa 073b — Labores culturais: non borrar o que ten labores

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 073. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Cultivos, parcelas e explotacións con labores rexistrados non se poden borrar (conservación de 3 anos), como coas regas. Deseño: `docs/superpowers/specs/2026-10-25-labores-culturais-design.md`

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `src/horta/services/parcelas.py`
- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.models.horta import RolHorta
```

Despois:
```python
from horta.models.horta import RolHorta
from horta.models.labor import Labor
```

### Paso 2 — `src/horta/services/cultivos.py`

Antes:
```python
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
```

Despois:
```python
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Labor).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten labores rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
```

### Paso 3 — `src/horta/services/parcelas.py`

Antes:
```python
from horta.models.horta import RolHorta
```

Despois:
```python
from horta.models.horta import RolHorta
from horta.models.labor import Labor
```

### Paso 4 — `src/horta/services/parcelas.py`

Antes:
```python
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
```

Despois:
```python
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if ids_cultivos and session.query(Labor).filter(Labor.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten labores rexistrados e debe conservarse (obriga legal)."
        )
```

### Paso 5 — `src/horta/services/hortas.py`

Antes:
```python
from horta.models.horta import Horta, HortaMembro, RolHorta
```

Despois:
```python
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.labor import Labor
```

### Paso 6 — `src/horta/services/hortas.py`

Antes:
```python
            "Esta explotación ten regas rexistradas e debe conservarse (obriga legal)."
        )
```

Despois:
```python
            "Esta explotación ten regas rexistradas e debe conservarse (obriga legal)."
        )
    if session.query(Labor).filter_by(horta_id=horta.id).first():
        raise OperacionNonPermitidaError(
            "Esta explotación ten labores rexistrados e debe conservarse (obriga legal)."
        )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os labores consérvanse.
