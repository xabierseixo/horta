# Tarefa 072g — Comando horta-catalogos (1/2)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Primeira parte do comando novo: importa por defecto os catálogos que leva a app, revisando antes. Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/cli_catalogos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/cli_catalogos.py`

Antes:
```python
"""horta-catalogos: importa os catálogos oficiais do FEGA descargados do portal SIEX."""

from __future__ import annotations

import argparse
from pathlib import Path

from horta.db import get_session
from horta.services.catalogos import cargar_nomes_galegos
from horta.services.catalogos_importar import (
    CATALOGOS_XERAIS,
    InformeImportacion,
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes_importar import importar_fertilizantes
from horta.services.fito_importar import importar_fitosanitarios
```

Despois:
```python
"""horta-catalogos: importa os catálogos oficiais do FEGA e o rexistro de fitosanitarios do MAPA."""

from __future__ import annotations

import argparse
from pathlib import Path

from horta.db import get_session
from horta.services.catalogos import cargar_nomes_galegos
from horta.services.catalogos_ficheiros import DIRECTORIO_APP, Revision, revisar
from horta.services.catalogos_importar import InformeImportacion
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_importar import importar_fitosanitarios
```

### Paso 2 — `src/horta/cli_catalogos.py`

Antes:
```python
def _importar(directorio: Path) -> int:
    with get_session() as session:
        cultivos = directorio / "PRODUCTOS.xlsx"
        if cultivos.exists():
            _imprimir(importar_cultivos(session, cultivos))
        variedades = directorio / "VARIEDAD_ESPECIE_TIPO.xlsx"
        if variedades.exists():
            try:
                _imprimir(importar_variedades(session, variedades))
            except OperacionNonPermitidaError as erro:
                print(f"variedade: {erro}")
        fertilizantes = directorio / "DETALLE_MATERIAL_FERT.xlsx"
        if fertilizantes.exists():
            _imprimir(importar_fertilizantes(session, fertilizantes))
        for clave, (ficheiro, _, _) in CATALOGOS_XERAIS.items():
            ruta = directorio / f"{ficheiro}.xlsx"
            if ruta.exists():
                _imprimir(importar_catalogo(session, clave, ruta))
            else:
                print(f"{clave}: falta {ruta.name}")
    return 0
```

Despois:
```python
def _con_problemas(revisions: list[Revision]) -> list[Revision]:
    return [r for r in revisions if r.catalogo is not None
            and (r.erro or (r.informe is not None and r.informe.sospeitoso))]


def _importar(directorio: Path | None, forzar: bool) -> int:
    rutas = sorted((directorio or DIRECTORIO_APP).glob("*.xlsx"))
    with get_session() as session:
        # Primeiro revísase sen gardar: un ficheiro con erros ou sospeitoso detén todo
        problemas = _con_problemas(revisar(session, rutas))
        for r in problemas:
            if r.erro or r.informe is None:
                print(f"{r.ficheiro}: {r.erro}")
            else:
                print(f"{r.ficheiro}: daría de baixa {r.informe.baixas} de "
                      f"{r.informe.existentes} códigos (usa --forzar se é correcto)")
        if problemas and not forzar:
            return 1
        revisions = revisar(session, rutas, aplicar=True)
    for r in revisions:
        if r.informe is not None:
            _imprimir(r.informe)
        elif r.catalogo is not None:
            print(f"{r.ficheiro}: {r.erro}")
    ignorados = sum(r.catalogo is None for r in revisions)
    if ignorados:
        print(f"{ignorados} ficheiros non son catálogos dos que usa a app")
    return 1 if _con_problemas(revisions) else 0
```

### Paso 3 — `src/horta/cli_catalogos.py`

Antes:
```python
    p_imp = sub.add_parser("importar", help="importa os XLSX dun directorio")
    p_imp.add_argument("directorio", type=Path)
```

Despois:
```python
    p_imp = sub.add_parser("importar", help="importa os XLSX do FEGA (por defecto, os da app)")
    p_imp.add_argument("directorio", type=Path, nargs="?", default=None)
    p_imp.add_argument("--forzar", action="store_true",
                       help="importar aínda que un ficheiro dea de baixa moitos códigos")
```

### Paso 4 — `src/horta/cli_catalogos.py`

Antes:
```python
    if args.orde == "importar":
        return _importar(args.directorio)
```

Despois:
```python
    if args.orde == "importar":
        return _importar(args.directorio, args.forzar)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Comando horta-catalogos (1/2): feito.
