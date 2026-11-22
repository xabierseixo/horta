# Tarefa 075h2 — Quen e horas: o labor esixe quen

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075h. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar un labor esixe quen o fixo (da explotación) e garda as horas. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/labores.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/labores.py`

Antes:
```python
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen
```

### Paso 2 — `src/horta/services/labores.py`

Antes:
```python
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
```

Despois:
```python
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

### Paso 3 — `src/horta/services/labores.py`

Antes:
```python
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
    if datos.persoa_id is not None:
        persoa = session.get(Persoa, datos.persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")
```

Despois:
```python
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
```

### Paso 4 — `src/horta/services/labores.py`

Antes:
```python
    labor.persoa_id = datos.persoa_id
```

Despois:
```python
    labor.persoa_id = datos.persoa_id
    labor.horas = datos.horas
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: o labor esixe quen: feito.
