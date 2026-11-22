# Tarefa 050d — Servizos sen a fertilización vella

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 050c. **Axente**: qwen-66 (mantemento).

## Obxectivo

A fertilización vella (`Fertilizacion`, táboa `fertilizacion`) xa non a usa ningunha pantalla nin proba: a sección Fertilización usa os abonados novos. Paso 4: borrar cultivo, parcela ou explotación xa non busca fertilizacións vellas.

## Ficheiros a tocar

- `src/horta/services/parcelas.py`
- `src/horta/services/cultivos.py`
- `src/horta/services/hortas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/parcelas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 2 — `src/horta/services/parcelas.py`: non buscar fertilizacións vellas

Antes:
```python
    for cultivo in cultivos:
        for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
            session.delete(fertilizacion)
    # Igual que en eliminar_horta: sen relationship(), forzar estes borrados
    # á BD antes de borrar os seus Cultivo pai.
    session.flush()
    for cultivo in cultivos:
```

Despois:
```python
    for cultivo in cultivos:
```

### Paso 3 — `src/horta/services/cultivos.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 4 — `src/horta/services/cultivos.py`: non buscar fertilizacións vellas

Antes:
```python
    for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
        session.delete(fertilizacion)
    session.flush()
```

Despois:
```python
    session.flush()
```

### Paso 5 — `src/horta/services/hortas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 6 — `src/horta/services/hortas.py`: non buscar fertilizacións vellas

Antes:
```python
    cultivo_ids = [c.id for c in cultivos]
    if cultivo_ids:
        for fertilizacion in (
            session.query(Fertilizacion).filter(Fertilizacion.cultivo_id.in_(cultivo_ids)).all()
        ):
            session.delete(fertilizacion)
        # Igual que en eliminar_parcela: sen relationship(), forzar estes
        # borrados á BD antes de borrar os seus Cultivo pai.
        session.flush()
    for cultivo in cultivos:
```

Despois:
```python
    for cultivo in cultivos:
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os servizos xa non usan a fertilización vella.
