# Tarefa 072a2 — Catálogos: importación segura (3/4, variedades)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As variedades comproban as columnas e admiten o modo revisión. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/catalogos_importar.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    _, filas = _ler_xlsx(ruta)
```

Despois:
```python
    cabeceira, filas = _ler_xlsx(ruta)
    _comprobar_columnas(ruta, cabeceira, ["Código cultivo", "Código Variedad/ Especie/ Tipo",
                                          "Variedad/ Especie/ Tipo"])
```

### Paso 2 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    existentes = {(v.cultivo_codigo, v.codigo): v for v in session.query(VariedadeSiex)}
```

Despois:
```python
    existentes = {(v.cultivo_codigo, v.codigo): v for v in session.query(VariedadeSiex)}
    informe.existentes = len(existentes)
```

### Paso 3 — `src/horta/services/catalogos_importar.py`

Antes:
```python
            informe.baixas += 1
    session.commit()
```

Despois:
```python
            informe.baixas += 1
    _rematar(session, aplicar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Catálogos: importación segura (3/4, variedades): feito.
