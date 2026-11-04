"""Tarefas da app en segundo plano: catálogos na primeira instalación, rexistro do MAPA
e copia de seguridade diaria.

Van dentro da app para que funcionen onde se desprega, sen programar nada no servidor.
HORTA_ACTUALIZAR=0 desactiva as actualizacións (probas, equipos sen internet) e
HORTA_COPIAS=0 as copias.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime

from loguru import logger
from nicegui import app, background_tasks, run

from horta.db import engine, get_session
from horta.services.catalogos_ficheiros import importar_da_app, sen_catalogos
from horta.services.copias import copia_diaria
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_descargar import actualizar_fitosanitarios

INTERVALO_SEGUNDOS = 6 * 3600
INTERVALO_COPIAS_SEGUNDOS = 3600


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


async def _bucle_copias() -> None:
    while True:
        try:
            ruta = await run.io_bound(copia_diaria, engine, datetime.now())
            if ruta is not None:
                logger.info("Copia de seguridade: {}", ruta)
        except Exception:
            logger.exception("Fallou a copia de seguridade")
        await asyncio.sleep(INTERVALO_COPIAS_SEGUNDOS)


def activar() -> None:
    if os.environ.get("HORTA_ACTUALIZAR", "1") != "0":
        app.on_startup(lambda: background_tasks.create(_bucle(), name="actualizacions"))
    if os.environ.get("HORTA_COPIAS", "1") != "0":
        app.on_startup(lambda: background_tasks.create(_bucle_copias(), name="copias"))
