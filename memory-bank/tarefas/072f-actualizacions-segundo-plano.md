# Tarefa 072f — App: actualizacións en segundo plano

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 072e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Ao arrancar e cada 6 h, a app importa os catálogos que leva se a BD non ten ningún e comproba o rexistro do MAPA. HORTA_ACTUALIZAR=0 desactívao. Probado: ao arrancar actualizou o rexistro (13 altas, 2 baixas, 99 cambios). Deseño: `docs/superpowers/specs/2026-10-25-catalogos-actualizacion-design.md`

## Ficheiros a tocar

- `src/horta/actualizacions.py` (**ficheiro novo**)
- `src/horta/main.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/actualizacions.py`

Contido completo:
```python
"""Tarefas da app en segundo plano: catálogos na primeira instalación e rexistro do MAPA.

Van dentro da app para que funcionen onde se desprega, sen programar nada no servidor.
HORTA_ACTUALIZAR=0 desactívaas (probas, equipos sen internet).
"""

from __future__ import annotations

import asyncio
import os

from loguru import logger
from nicegui import app, background_tasks, run

from horta.db import get_session
from horta.services.catalogos_ficheiros import importar_da_app, sen_catalogos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_descargar import actualizar_fitosanitarios

INTERVALO_SEGUNDOS = 6 * 3600


def ciclo() -> None:
    with get_session() as session:
        if sen_catalogos(session):
            for revision in importar_da_app(session):
                if revision.erro:
                    logger.error("Catálogo {}: {}", revision.ficheiro, revision.erro)
            logger.info("Importados os catálogos oficiais que leva a app")
        try:
            informe = actualizar_fitosanitarios(session)
        except OperacionNonPermitidaError as erro:
            logger.warning("{}", erro)
            return
        if informe is not None and not informe.xa_importado:
            logger.info("Rexistro do MAPA: {} altas, {} baixas, {} cambios",
                        informe.altas, informe.baixas, informe.cambios)


async def _bucle() -> None:
    while True:
        try:
            await run.io_bound(ciclo)
        except Exception:
            logger.exception("Fallou a actualización dos catálogos")
        await asyncio.sleep(INTERVALO_SEGUNDOS)


def activar() -> None:
    if os.environ.get("HORTA_ACTUALIZAR", "1") == "0":
        return
    app.on_startup(lambda: background_tasks.create(_bucle(), name="actualizacions"))
```

### Paso 2 — `src/horta/main.py`

Antes:
```python
from starlette.middleware.base import BaseHTTPMiddleware

```

Despois:
```python
from starlette.middleware.base import BaseHTTPMiddleware

from horta.actualizacions import activar as activar_actualizacions
```

### Paso 3 — `src/horta/main.py`

Antes:
```python
def main() -> None:
```

Despois:
```python
def main() -> None:
    activar_actualizacions()
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

App: actualizacións en segundo plano: feito.
