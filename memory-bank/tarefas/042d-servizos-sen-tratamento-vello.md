# Tarefa 042d — Servizos sen o tratamento vello

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 042c.

## Obxectivo

O modelo vello `Tratamento` (táboa `tratamento`) xa non o usa ningunha pantalla: os datos pasaron a `TratamentoFito` (caderno CUE). Esta cola quítao sen perder nada. Paso 4 de 5: borrar parcela, cultivo ou horta xa non busca tratamentos vellos.

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
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 2 — `src/horta/services/parcelas.py`: non buscar tratamentos vellos

Antes:
```python
    for cultivo in cultivos:
        for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
            session.delete(tratamento)
        for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
```

Despois:
```python
    for cultivo in cultivos:
        for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
```

### Paso 3 — `src/horta/services/cultivos.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 4 — `src/horta/services/cultivos.py`: non buscar tratamentos vellos

Antes:
```python
    for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
        session.delete(tratamento)
```

Despois:
```python
```

### Paso 5 — `src/horta/services/hortas.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 6 — `src/horta/services/hortas.py`: non buscar tratamentos vellos

Antes:
```python
    if cultivo_ids:
        for tratamento in (
            session.query(Tratamento).filter(Tratamento.cultivo_id.in_(cultivo_ids)).all()
        ):
            session.delete(tratamento)
        for fertilizacion in (
```

Despois:
```python
    if cultivo_ids:
        for fertilizacion in (
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Os servizos de parcelas, cultivos e hortas xa non usan o modelo vello `Tratamento`.
