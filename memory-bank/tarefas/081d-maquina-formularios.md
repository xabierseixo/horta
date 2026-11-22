# Tarefa 081d — Parte común (5/9): máquina nos formularios

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Campo «Máquina» nos formularios de rega, tratamento en instalacións, entradas e saídas e produción. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `src/horta/ui/pages/regas.py`
- `src/horta/ui/pages/tratamentos_instalacion.py`
- `src/horta/ui/pages/movementos_animais.py`
- `src/horta/ui/pages/producions_animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
```

### Paso 2 — `src/horta/ui/pages/regas.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 3 — `src/horta/ui/pages/regas.py`

Antes:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
```

Despois:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
```

### Paso 4 — `src/horta/ui/pages/regas.py`

Antes:
```python
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value))
```

Despois:
```python
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value)
```

### Paso 5 — `src/horta/ui/pages/regas.py`

Antes:
```python
        horas.value = f"{r.horas:g}" if r and r.horas else ""
```

Despois:
```python
        horas.value = f"{r.horas:g}" if r and r.horas else ""
        maquina.value = r.maquina_id if r and r.maquina_id in maquinas else None
```

### Paso 6 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
```

### Paso 7 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 8 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        horas = ui.input("Horas de traballo").classes("w-full")
```

Despois:
```python
        horas = ui.input("Horas de traballo").classes("w-full")
        maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
```

### Paso 9 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value))
```

Despois:
```python
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value)
```

### Paso 10 — `src/horta/ui/pages/tratamentos_instalacion.py`

Antes:
```python
        horas.value = f"{t.horas:g}" if t and t.horas else ""
```

Despois:
```python
        horas.value = f"{t.horas:g}" if t and t.horas else ""
        maquina.value = t.maquina_id if t and t.maquina_id in maquinas else None
```

### Paso 11 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
```

### Paso 12 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 13 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
```

Despois:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
```

### Paso 14 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
```

Despois:
```python
                        horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None)
```

### Paso 15 — `src/horta/ui/pages/movementos_animais.py`

Antes:
```python
        horas.value = f"{mo.horas:g}" if mo and mo.horas else ""
```

Despois:
```python
        horas.value = f"{mo.horas:g}" if mo and mo.horas else ""
        maquina.value = mo.maquina_id if mo and mo.maquina_id in maquinas else None
```

### Paso 16 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
```

### Paso 17 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
```

### Paso 18 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
```

Despois:
```python
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
```

### Paso 19 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
```

Despois:
```python
                        horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None)
```

### Paso 20 — `src/horta/ui/pages/producions_animais.py`

Antes:
```python
        horas.value = f"{pr.horas:g}" if pr and pr.horas else ""
```

Despois:
```python
        horas.value = f"{pr.horas:g}" if pr and pr.horas else ""
        maquina.value = pr.maquina_id if pr and pr.maquina_id in maquinas else None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (5/9): máquina nos formularios: feito.
