# Tarefa 015 — Deseño novo: táboas e avisos de persoas, maquinaria e tratamentos

**Estado**: feita

**Rama**: `deseno-visual`. Guía: `docs/superpowers/specs/2026-10-22-deseno-visual-design.md`.

## Obxectivo

Mesmo estilo de táboa ca no resto da app e avisos de carné ROPO coa caixa `aviso`.

## Ficheiros a tocar

- `src/horta/ui/pages/persoas.py`
- `src/horta/ui/pages/maquinaria.py`
- `src/horta/ui/pages/tratamentos_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/persoas.py`: táboa

Antes:
```python
    ).classes("w-full").props('no-data-label="Aínda non hai persoas rexistradas"')
```
Despois:
```python
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai persoas rexistradas"'
    )
```

### Paso 2 — mesmo ficheiro: aviso de carné caducado

Antes:
```python
                    .classes("text-negative")
```
Despois:
```python
                    .classes("aviso w-full")
```

### Paso 3 — mesmo ficheiro: aviso de carné que vai caducar

Antes:
```python
                    "text-warning"
```
Despois:
```python
                    "aviso w-full"
```

### Paso 4 — `src/horta/ui/pages/maquinaria.py`: táboa

Antes:
```python
        rows=filas, row_key="id",
    ).classes("w-full")
```
Despois:
```python
        rows=filas, row_key="id",
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai máquinas rexistradas"'
    )
```

### Paso 5 — `src/horta/ui/pages/tratamentos_fito.py`: táboa

Antes:
```python
    ).classes("w-full").props('no-data-label="Aínda non hai tratamentos rexistrados"')
```
Despois:
```python
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai tratamentos rexistrados"'
    )
```

## Criterios de aceptación

- As tres táboas teñen a clase `taboa` e as props `flat bordered`.
- Os dous avisos de carné usan a clase `aviso`.
- Non se cambiou ningún outro ficheiro.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

- **Paso 1** (persoas.py liña 52): `.classes("w-full")` → `.classes("w-full taboa").props('flat bordered no-data-label="Aínda non hai persoas rexistradas"')` ✅
- **Paso 2** (persoas.py liña 31): `.classes("text-negative")` → `.classes("aviso w-full")` ✅
- **Paso 3** (persoas.py liña 34): `"text-warning"` → `"aviso w-full"` ✅
- **Paso 4** (maquinaria.py liña 32): `.classes("w-full")` → `.classes("w-full taboa").props('flat bordered no-data-label="Aínda non hai máquinas rexistradas"')` ✅
- **Paso 5** (tratamentos_fito.py liña 88): `.classes("w-full").props('no-data-label="Aínda non hai tratamentos rexistrados"')` → `.classes("w-full taboa").props('flat bordered no-data-label="Aínda non hai tratamentos rexistrados"')` ✅

**Comprobacións**:
- `uv run ruff check src tests`: All checks passed!
- `uv run mypy src`: Success: no issues found in 51 source files
- `uv run pytest -q`: 237 passed in 16.80s

**Commit**: `5296f51` — `feat: deseño táboas e avisos persoas maquinaria tratamentos Axente: smoth`
