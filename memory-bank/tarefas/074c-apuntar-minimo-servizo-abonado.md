# Tarefa 074c — Apuntar o mínimo (4/6): servizo de abonado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 074b. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Apuntar un abonado só esixe cultivo, data e abono. Tipo, método, boas prácticas, dose e superficie son opcionais. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/services/abonados.py`
- `tests/services/test_abonados.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/abonados.py`

Antes:
```python
    tipo_fertilizacion: str
    metodo: str
```

Despois:
```python
    tipo_fertilizacion: str | None = None
    metodo: str | None = None
```

### Paso 2 — `src/horta/services/abonados.py`

Antes:
```python
    elif not cultivo.superficie_ha:
        raise OperacionNonPermitidaError("Indica a superficie: o cultivo non a ten")
    validar_codigo(session, "tipo_fertilizacion", datos.tipo_fertilizacion, datos.data_inicio)
    validar_codigo(session, "metodo_fertilizacion", datos.metodo, datos.data_inicio)
    if not datos.boas_practicas:
        raise OperacionNonPermitidaError(
            "Indica polo menos unha boa práctica (ou «Non realiza boas prácticas»)"
        )
```

Despois:
```python
    if datos.tipo_fertilizacion:
        validar_codigo(session, "tipo_fertilizacion", datos.tipo_fertilizacion, datos.data_inicio)
    if datos.metodo:
        validar_codigo(session, "metodo_fertilizacion", datos.metodo, datos.data_inicio)
```

### Paso 3 — `src/horta/services/abonados.py`

Antes:
```python
    if datos.dose is None or datos.dose <= 0:
```

Despois:
```python
    if datos.dose is None:
        return
    if datos.dose <= 0:
```

### Paso 4 — `src/horta/services/abonados.py`

Antes:
```python
    abonado.superficie_ha = datos.superficie_ha or cultivo.superficie_ha or 0
    abonado.fertilizante_id = datos.fertilizante_id
    abonado.dose = datos.dose if datos.fertilizante_id else None
    abonado.unidade = datos.unidade if datos.fertilizante_id else None
    abonado.tipo_fertilizacion = datos.tipo_fertilizacion
    abonado.metodo = datos.metodo
```

Despois:
```python
    abonado.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    abonado.fertilizante_id = datos.fertilizante_id
    abonado.dose = datos.dose if datos.fertilizante_id else None
    abonado.unidade = datos.unidade if datos.fertilizante_id and datos.dose else None
    abonado.tipo_fertilizacion = datos.tipo_fertilizacion or None
    abonado.metodo = datos.metodo or None
```

### Paso 5 — `tests/services/test_abonados.py`

Antes:
```python
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
    ({"boas_practicas": []}, "boa práctica"),
```

Despois:
```python
    ({"superficie_ha": 0.3}, "maior ca do cultivo"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (4/6): servizo de abonado: feito.
