# Tarefa 053c — Análises ao borrar cultivos e parcelas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 053. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As análises son voluntarias (CUE: «en caso de haberse realizado»): borrar un cultivo ou unha parcela non se bloquea, pero a análise consérvase na explotación sen esa ligazón. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §5. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/services/cultivos.py`
- `src/horta/services/parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/cultivos.py`: importar

Antes:
```python
from horta.models.abonado import Abonado
```

Despois:
```python
from horta.models.abonado import Abonado
from horta.models.analise import Analise
```

### Paso 2 — `src/horta/services/cultivos.py`: soltar a análise do cultivo

Antes:
```python
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
```

Despois:
```python
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
    session.query(Analise).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
```

### Paso 3 — `src/horta/services/parcelas.py`: importar

Antes:
```python
from horta.models.abonado import Abonado
```

Despois:
```python
from horta.models.abonado import Abonado
from horta.models.analise import Analise
```

### Paso 4 — `src/horta/services/parcelas.py`: soltar a análise da parcela e dos seus cultivos

Antes:
```python
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
```

Despois:
```python
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    session.query(Analise).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    if ids_cultivos:
        session.query(Analise).filter(Analise.cultivo_id.in_(ids_cultivos)).update(
            {"cultivo_id": None})
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Ao borrar un cultivo ou parcela, as súas análises quedan na explotación.
