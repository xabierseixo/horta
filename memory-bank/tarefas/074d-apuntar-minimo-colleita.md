# Tarefa 074d — Apuntar o mínimo (5/6): lote automático na colleita

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074c. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Se a colleita se apunta sen lote, ponse o seguinte libre (AAAA-CULTIVO-NNN). Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/services/colleitas.py`
- `tests/services/test_colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/colleitas.py`

Antes:
```python
        raise OperacionNonPermitidaError("O lote é obrigatorio")
```

Despois:
```python
        raise OperacionNonPermitidaError("O lote non pode quedar baleiro")
```

### Paso 2 — `src/horta/services/colleitas.py`

Antes:
```python
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
```

Despois:
```python
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, datos.cultivo_id, datos.data)
```

### Paso 3 — `tests/services/test_colleitas.py`

Antes:
```python
        ({"superficie_ha": 0.9}, "maior ca do cultivo"),
        ({"lote": "  "}, "lote é obrigatorio"),
```

Despois:
```python
        ({"superficie_ha": 0.9}, "maior ca do cultivo"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (5/6): lote automático na colleita: feito.
