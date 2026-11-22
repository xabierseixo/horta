# Tarefa 075j — Quen e horas: a toma de mostras esixe quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075i. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar unha toma de mostras esixe quen a colleu e garda as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/analises.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/analises.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/analises.py`

Antes:
```python
        raise OperacionNonPermitidaError("A data da mostra non pode ser futura")
```

Despois:
```python
        raise OperacionNonPermitidaError("A data da mostra non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 3 — `src/horta/services/analises.py`

Antes:
```python
    analise.colleita_id = datos.colleita_id
```

Despois:
```python
    analise.colleita_id = datos.colleita_id
    analise.persoa_id = datos.persoa_id
    analise.horas = datos.horas
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: a toma de mostras esixe quen: feito.
