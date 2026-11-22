# Tarefa 072 — Catálogos: importación segura (1/4, comprobación de columnas)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Primeira parte: o informe sabe cantos códigos había e marca como sospeitoso un ficheiro que daría de baixa moitos; función que comproba as columnas e función que remata gardando ou só revisando. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/services/catalogos_importar.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    xa_importado: bool = False
```

Despois:
```python
    xa_importado: bool = False
    existentes: int = 0

    @property
    def sospeitoso(self) -> bool:
        """Moitas baixas dunha vez: o típico dun ficheiro equivocado ou cun formato novo."""
        return self.baixas > 5 and self.baixas > 0.2 * self.existentes


def _comprobar_columnas(ruta: Path, cabeceira: list[str], columnas: list[str]) -> None:
    for columna in columnas:
        if columna not in cabeceira:
            raise OperacionNonPermitidaError(
                f"Ao ficheiro {ruta.name} fáltalle a columna «{columna}». O FEGA puido cambiar "
                "o formato: hai que adaptar a app."
            )


def _rematar(session: Session, aplicar: bool) -> None:
    """Garda a importación. En modo revisión só a envía á BD sen gardala: quen revisa un lote
    desfaino todo ao final (as variedades precisan ver os cultivos do mesmo lote)."""
    if aplicar:
        session.commit()
    else:
        session.flush()
```

### Paso 2 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    session: Session, catalogo: str, ruta: Path, hoxe: date | None = None
```

Despois:
```python
    session: Session, catalogo: str, ruta: Path, hoxe: date | None = None,
    aplicar: bool = True,
```

### Paso 3 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    cabeceira, filas = _ler_xlsx(ruta)
```

Despois:
```python
    cabeceira, filas = _ler_xlsx(ruta)
    _comprobar_columnas(ruta, cabeceira, [columna_codigo] + (
        [columna_descricion] if columna_descricion else []))
```

### Paso 4 — `src/horta/services/catalogos_importar.py`

Antes:
```python
    existentes = {v.codigo: v for v in session.query(CatalogoValor).filter_by(catalogo=catalogo)}
```

Despois:
```python
    existentes = {v.codigo: v for v in session.query(CatalogoValor).filter_by(catalogo=catalogo)}
    informe.existentes = len(existentes)
```

### Paso 5 — `src/horta/services/catalogos_importar.py`

Antes:
```python
            valor.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
```

Despois:
```python
            valor.data_baixa = hoxe
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

Catálogos: importación segura (1/4, comprobación de columnas): feito.
