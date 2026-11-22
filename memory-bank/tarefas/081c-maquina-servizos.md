# Tarefa 081c — Parte común (4/9): gardar a máquina

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os catro traballos gardan a máquina e comproban que é da explotación. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `src/horta/services/regas.py`
- `src/horta/services/tratamentos_instalacion.py`
- `src/horta/services/movementos_animais.py`
- `src/horta/services/producions_animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/regas.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
```

### Paso 2 — `src/horta/services/regas.py`

Antes:
```python
    horas: float | None = None
```

Despois:
```python
    horas: float | None = None
    maquina_id: int | None = None
```

### Paso 3 — `src/horta/services/regas.py`

Antes:
```python
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, horta_id, datos.maquina_id)
```

### Paso 4 — `src/horta/services/regas.py`

Antes:
```python
    rega.horas = datos.horas
```

Despois:
```python
    rega.horas = datos.horas
    rega.maquina_id = datos.maquina_id
```

### Paso 5 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
```

### Paso 6 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python


def _validar(session: Session, datos: DatosTratamentoInstalacion, horta_id: int,
             hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    maquina_id: int | None = None


def _validar(session: Session, datos: DatosTratamentoInstalacion, horta_id: int,
             hoxe: date) -> None:
    if datos.tipo not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle se é postcolleita, local ou transporte")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data do tratamento non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, horta_id, datos.maquina_id)
```

### Paso 7 — `src/horta/services/movementos_animais.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
```

### Paso 8 — `src/horta/services/movementos_animais.py`

Antes:
```python
    notas: str | None = None
```

Despois:
```python
    notas: str | None = None
    maquina_id: int | None = None
```

### Paso 9 — `src/horta/services/movementos_animais.py`

Antes:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, animal.horta_id, datos.maquina_id)
```

### Paso 10 — `src/horta/services/movementos_animais.py`

Antes:
```python
    mov.horas = datos.horas
```

Despois:
```python
    mov.horas = datos.horas
    mov.maquina_id = datos.maquina_id
```

### Paso 11 — `src/horta/services/producions_animais.py`

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import comprobar_rol_horta
from horta.services.maquinaria import comprobar_maquina
```

### Paso 12 — `src/horta/services/producions_animais.py`

Antes:
```python
    notas: str | None = None
```

Despois:
```python
    notas: str | None = None
    maquina_id: int | None = None
```

### Paso 13 — `src/horta/services/producions_animais.py`

Antes:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    comprobar_quen(session, animal.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, animal.horta_id, datos.maquina_id)
```

### Paso 14 — `src/horta/services/producions_animais.py`

Antes:
```python
    pr.horas = datos.horas
```

Despois:
```python
    pr.horas = datos.horas
    pr.maquina_id = datos.maquina_id
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (4/9): gardar a máquina: feito.
