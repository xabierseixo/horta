# Tarefa 074b — Apuntar o mínimo (3/6): servizos de rega e labor

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar unha rega só esixe cultivo e data; un labor, cultivo, data e tipo. O resto, se se indica, compróbase igual ca antes. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/services/regas.py`
- `src/horta/services/labores.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/regas.py`

Antes:
```python
    sistema_rega: str
    cantidade: float
```

Despois:
```python
    sistema_rega: str | None = None
    cantidade: float | None = None
```

### Paso 2 — `src/horta/services/regas.py`

Antes:
```python
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
    if datos.cantidade is None or datos.cantidade <= 0:
```

Despois:
```python
    if datos.cantidade is not None and datos.cantidade <= 0:
```

### Paso 3 — `src/horta/services/regas.py`

Antes:
```python
    validar_codigo(session, "sistema_rega", datos.sistema_rega, datos.data_inicio)
```

Despois:
```python
    if datos.sistema_rega:
        validar_codigo(session, "sistema_rega", datos.sistema_rega, datos.data_inicio)
```

### Paso 4 — `src/horta/services/regas.py`

Antes:
```python
    rega.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
    rega.sistema_rega = datos.sistema_rega
```

Despois:
```python
    rega.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    rega.sistema_rega = datos.sistema_rega or None
```

### Paso 5 — `src/horta/services/labores.py`

Antes:
```python
            raise OperacionNonPermitidaError("A superficie do labor é maior ca do cultivo")
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
```

Despois:
```python
            raise OperacionNonPermitidaError("A superficie do labor é maior ca do cultivo")
```

### Paso 6 — `src/horta/services/labores.py`

Antes:
```python
    labor.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
```

Despois:
```python
    labor.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (3/6): servizos de rega e labor: feito.
