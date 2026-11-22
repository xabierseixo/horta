# Tarefa 075c — Quen e horas: as probas indican quen (1/5)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As probas de rega, labor e abonado indican quen fixo o traballo. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `tests/services/test_regas.py`
- `tests/services/test_labores.py`
- `tests/services/test_abonados.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `tests/services/test_regas.py`

Antes:
```python
    ultimo_sistema_rega,
)
```

Despois:
```python
    ultimo_sistema_rega,
)

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 2 — `tests/services/test_regas.py`

Antes:
```python
    return DatosRega(**base)
```

Despois:
```python
    return DatosRega(**{"persoa_id": QUEN, **base})
```

### Paso 3 — `tests/services/test_labores.py`

Antes:
```python
from horta.services.parcelas import crear_parcela, eliminar_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela, eliminar_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 4 — `tests/services/test_labores.py`

Antes:
```python
    return DatosLabor(**base)
```

Despois:
```python
    return DatosLabor(**{"persoa_id": QUEN, **base})
```

### Paso 5 — `tests/services/test_abonados.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

```

### Paso 6 — `tests/services/test_abonados.py`

Antes:
```python
    return DatosAbonado(**base)
```

Despois:
```python
    return DatosAbonado(**{"aplicador_persoa_id": QUEN, **base})
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas: as probas indican quen (1/5): feito.
