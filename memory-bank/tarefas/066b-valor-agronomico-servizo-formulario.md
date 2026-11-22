# Tarefa 066b — Abonos: valor agronómico no servizo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 066. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O servizo valida as riquezas (0–100 %) e os metais (non negativos) e copia as formas do N do catálogo. Deseño: `docs/superpowers/specs/2026-10-25-caderno-completo-design.md`

## Ficheiros a tocar

- `src/horta/services/fertilizantes.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/fertilizantes.py`

Antes:
```python
UNIDADES_DOSE = (*_MASA_A_KG_HA, *_VOLUME_A_L_HA)
```

Despois:
```python
UNIDADES_DOSE = (*_MASA_A_KG_HA, *_VOLUME_A_L_HA)
FORMAS_N_P = ("n_organico_pct", "n_ureico_pct", "n_nitrico_pct", "n_amoniacal_pct",
              "p2o5_soluble_pct")
METAIS_RESIDUO = ("cadmio", "cobre", "niquel", "chumbo", "zinc", "mercurio", "cromo_vi",
                  "arsenico", "cromo")
```

### Paso 2 — `src/horta/services/fertilizantes.py`

Antes:
```python
    k2o_pct: float | None = None
```

Despois:
```python
    k2o_pct: float | None = None
    n_organico_pct: float | None = None
    n_ureico_pct: float | None = None
    n_nitrico_pct: float | None = None
    n_amoniacal_pct: float | None = None
    p2o5_soluble_pct: float | None = None
    materia_organica_pct: float | None = None
    cadmio: float | None = None
    cobre: float | None = None
    niquel: float | None = None
    chumbo: float | None = None
    zinc: float | None = None
    mercurio: float | None = None
    cromo_vi: float | None = None
    arsenico: float | None = None
    cromo: float | None = None
```

### Paso 3 — `src/horta/services/fertilizantes.py`

Antes:
```python
    for riqueza in (datos.n_pct, datos.p2o5_pct, datos.k2o_pct):
```

Despois:
```python
    for riqueza in (datos.n_pct, datos.p2o5_pct, datos.k2o_pct, *(
            getattr(datos, c) for c in FORMAS_N_P), datos.materia_organica_pct):
```

### Paso 4 — `src/horta/services/fertilizantes.py`

Antes:
```python
            raise OperacionNonPermitidaError("A riqueza ten que estar entre 0 e 100 %")
```

Despois:
```python
            raise OperacionNonPermitidaError("A riqueza ten que estar entre 0 e 100 %")
    if any(getattr(datos, m) is not None and getattr(datos, m) < 0 for m in METAIS_RESIDUO):
        raise OperacionNonPermitidaError("Os metais pesados non poden ser negativos")
```

### Paso 5 — `src/horta/services/fertilizantes.py`

Antes:
```python
        n_pct=oficial.n_pct, p2o5_pct=oficial.p2o5_pct, k2o_pct=oficial.k2o_pct,
```

Despois:
```python
        n_pct=oficial.n_pct, p2o5_pct=oficial.p2o5_pct, k2o_pct=oficial.k2o_pct,
        **{c: getattr(oficial, c) or None for c in FORMAS_N_P},
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O servizo garda e valida o valor agronómico e os metais.
