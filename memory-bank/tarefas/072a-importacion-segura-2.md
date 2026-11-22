# Tarefa 072a — Catálogos: importación segura (2/4, catálogos xerais e cultivos)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Os catálogos xerais e os cultivos comproban as columnas e admiten o modo revisión (aplicar=False). Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/catalogos_importar.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos_importar.py`

Antes:
```python
def importar_cultivos(
    session: Session, ruta: Path, hoxe: date | None = None
```

Despois:
```python
def importar_cultivos(
    session: Session, ruta: Path, hoxe: date | None = None, aplicar: bool = True
```

### Paso 2 — `src/horta/services/catalogos_importar.py`

Antes:
```python
        return InformeImportacion(catalogo="cultivo", xa_importado=True)
    _, filas = _ler_xlsx(ruta)
```

Despois:
```python
        return InformeImportacion(catalogo="cultivo", xa_importado=True)
    cabeceira, filas = _ler_xlsx(ruta)
    _comprobar_columnas(ruta, cabeceira, ["Código", "Cultivo"])
```

### Paso 3 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    existentes = {c.codigo: c for c in session.query(CultivoSiex)}
```

Despois:
```python
    existentes = {c.codigo: c for c in session.query(CultivoSiex)}
    informe.existentes = len(existentes)
```

### Paso 4 — `src/horta/services/catalogos_importar.py`

Antes:
```python
            cultivo.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
```

Despois:
```python
            cultivo.data_baixa = hoxe
            informe.baixas += 1
    _rematar(session, aplicar)
```

### Paso 5 — `src/horta/services/catalogos_importar.py`

Antes:
```python
def importar_variedades(
    session: Session, ruta: Path, hoxe: date | None = None
```

Despois:
```python
def importar_variedades(
    session: Session, ruta: Path, hoxe: date | None = None, aplicar: bool = True
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Catálogos: importación segura (2/4, catálogos xerais e cultivos): feito.
