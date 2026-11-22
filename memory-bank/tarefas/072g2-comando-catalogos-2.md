# Tarefa 072g2 — Comando horta-catalogos (2/2, --forzar e --descargar)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

'importar' detense se un ficheiro ten erros ou é sospeitoso (salvo --forzar); 'fitosanitarios --descargar' descarga o rexistro do MAPA para o despregamento. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/cli_catalogos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/cli_catalogos.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_descargar import actualizar_fitosanitarios
```

### Paso 2 — `src/horta/cli_catalogos.py`

Antes:
```python
    return 1 if _con_problemas(revisions) else 0


```

Despois:
```python
    return 1 if _con_problemas(revisions) else 0


def _fitosanitarios(directorio: Path | None, descargar: bool) -> int:
    with get_session() as session:
        try:
            if descargar:
                informe = actualizar_fitosanitarios(session, forzar=True)
                assert informe is not None
            elif directorio is not None:
                informe = importar_fitosanitarios(session, directorio)
            else:
                print("Indica o directorio cos JSON do MAPA ou --descargar")
                return 2
        except OperacionNonPermitidaError as erro:
            print(f"fitosanitarios: {erro}")
            return 1
    _imprimir(informe)
    return 0


```

### Paso 3 — `src/horta/cli_catalogos.py`

Antes:
```python
    p_fito.add_argument("directorio", type=Path)
```

Despois:
```python
    p_fito.add_argument("directorio", type=Path, nargs="?", default=None)
    p_fito.add_argument("--descargar", action="store_true",
                        help="descargalo agora do MAPA (para o despregamento)")
```

### Paso 4 — `src/horta/cli_catalogos.py`

Antes:
```python
        with get_session() as session:
            try:
                _imprimir(importar_fitosanitarios(session, args.directorio))
            except OperacionNonPermitidaError as erro:
                print(f"fitosanitarios: {erro}")
                return 1
        return 0
```

Despois:
```python
        return _fitosanitarios(args.directorio, args.descargar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Comando horta-catalogos (2/2, --forzar e --descargar): feito.
