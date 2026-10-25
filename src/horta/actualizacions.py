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
