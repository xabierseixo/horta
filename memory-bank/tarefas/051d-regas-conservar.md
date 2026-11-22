# Tarefa 051d — Conservar cultivos e parcelas con regas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 051. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As regas son rexistros do caderno (CUE) e consérvanse: non se pode borrar un cultivo, parcela ou explotación que as teña (antes daría un erro da base de datos).

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `src/horta/services/parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: importar

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.rega import Rega
```

### Paso 2 — `src/horta/services/cultivos.py`: non borrar cultivos con regas

Antes:
```python
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
```

Despois:
```python
    if session.query(Rega).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten regas rexistradas e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
    if session.query(Colleita).filter_by(cultivo_id=cultivo.id).first():
```

### Paso 3 — `src/horta/services/parcelas.py`: importar

Antes:
```python
from horta.models.parcela import Parcela
```

Despois:
```python
from horta.models.parcela import Parcela
from horta.models.rega import Rega
```

### Paso 4 — `src/horta/services/parcelas.py`: non borrar parcelas con regas

Antes:
```python
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
```

Despois:
```python
    if ids_cultivos and session.query(Rega).filter(Rega.cultivo_id.in_(ids_cultivos)).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten regas rexistradas e debe conservarse (obriga legal)."
        )
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os cultivos e parcelas con regas non se poden borrar.
