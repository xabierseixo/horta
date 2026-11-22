# Tarefa 072a3 — Catálogos: importación segura (4/4, abonos)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072a2. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O catálogo de abonos comproba as columnas e admite o modo revisión. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/fertilizantes_importar.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    _codigo,
```

Despois:
```python
    _codigo,
    _comprobar_columnas,
```

### Paso 2 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    _nova_version,
```

Despois:
```python
    _nova_version,
    _rematar,
```

### Paso 3 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    session: Session, ruta: Path, hoxe: date | None = None
```

Despois:
```python
    session: Session, ruta: Path, hoxe: date | None = None, aplicar: bool = True
```

### Paso 4 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    _, filas = _ler_xlsx(ruta)
```

Despois:
```python
    cabeceira, filas = _ler_xlsx(ruta)
    _comprobar_columnas(ruta, cabeceira, ["C_FERTILIZANTE", "Código SIEX", "D_FERTILIZANTE_2",
                                          "N_% TOTAL", "P2O5 % total", "K2O % total"])
```

### Paso 5 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    existentes = {f.codigo: f for f in session.query(FertilizanteSiex)}
```

Despois:
```python
    existentes = {f.codigo: f for f in session.query(FertilizanteSiex)}
    informe.existentes = len(existentes)
```

### Paso 6 — `src/horta/services/fertilizantes_importar.py`

Antes:
```python
    session.commit()
```

Despois:
```python
    _rematar(session, aplicar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Catálogos: importación segura (4/4, abonos): feito.
