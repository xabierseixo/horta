# Tarefa 075i — Quen e horas: abonado e colleita esixen quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075h2. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar un abonado (salvo se o fixo unha empresa de servizos) ou unha colleita esixe quen o fixo e garda as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/abonados.py`
- `src/horta/services/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/abonados.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/abonados.py`

Antes:
```python
        raise OperacionNonPermitidaError("A data do abonado non pode ser futura")
```

Despois:
```python
        raise OperacionNonPermitidaError("A data do abonado non pode ser futura")
    # Se o fixo unha empresa de servizos, a persoa pode non ser do equipo
    comprobar_quen(session, horta_id, datos.aplicador_persoa_id, datos.horas,
                   obrigatoria=not datos.empresa_servizos_regfer)
```

### Paso 3 — `src/horta/services/abonados.py`

Antes:
```python
    abonado.aplicador_persoa_id = datos.aplicador_persoa_id
```

Despois:
```python
    abonado.aplicador_persoa_id = datos.aplicador_persoa_id
    abonado.horas = datos.horas
```

### Paso 4 — `src/horta/services/colleitas.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 5 — `src/horta/services/colleitas.py`

Antes:
```python
        raise OperacionNonPermitidaError("A data da colleita non pode ser futura")
```

Despois:
```python
        raise OperacionNonPermitidaError("A data da colleita non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 6 — `src/horta/services/colleitas.py`

Antes:
```python
    colleita.duracion_h_ha = datos.duracion_h_ha
```

Despois:
```python
    colleita.duracion_h_ha = datos.duracion_h_ha
    colleita.persoa_id = datos.persoa_id
    colleita.horas = datos.horas
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: abonado e colleita esixen quen: feito.
