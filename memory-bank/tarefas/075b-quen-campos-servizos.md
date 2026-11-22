# Tarefa 075b — Quen e horas: campos nos datos de cada traballo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os datos de cada tipo de traballo admiten quen o fixo e as horas (aínda non se esixe). Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/services/regas.py`
- `src/horta/services/labores.py`
- `src/horta/services/abonados.py`
- `src/horta/services/colleitas.py`
- `src/horta/services/analises.py`
- `src/horta/services/tratamentos_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/regas.py`

Antes:
```python
    num_contador: str | None = None
```

Despois:
```python
    num_contador: str | None = None
    persoa_id: int | None = None
    horas: float | None = None
```

### Paso 2 — `src/horta/services/labores.py`

Antes:
```python
    persoa_id: int | None = None
```

Despois:
```python
    persoa_id: int | None = None
    horas: float | None = None
```

### Paso 3 — `src/horta/services/abonados.py`

Antes:
```python
    aplicador_persoa_id: int | None = None
```

Despois:
```python
    aplicador_persoa_id: int | None = None
    horas: float | None = None
```

### Paso 4 — `src/horta/services/colleitas.py`

Antes:
```python
    duracion_h_ha: float | None = None
```

Despois:
```python
    duracion_h_ha: float | None = None
    persoa_id: int | None = None
    horas: float | None = None
```

### Paso 5 — `src/horta/services/analises.py`

Antes:
```python
    solo: dict[str, float | None] = field(default_factory=dict)
```

Despois:
```python
    solo: dict[str, float | None] = field(default_factory=dict)
    persoa_id: int | None = None
    horas: float | None = None
```

### Paso 6 — `src/horta/services/tratamentos_instalacion.py`

Antes:
```python
    notas: str | None = None
```

Despois:
```python
    notas: str | None = None
    persoa_id: int | None = None
    horas: float | None = None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: campos nos datos de cada traballo: feito.
