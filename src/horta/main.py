from __future__ import annotations

import re

from fastapi import Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from loguru import logger
from nicegui import Client, app, ui
from starlette.middleware.base import BaseHTTPMiddleware

from horta.actualizacions import activar as activar_actualizacions
from horta.log import configurar_rexistro
from horta.segredo import segredo_sesion
from horta.ui.erros import pagina_erro_html

RUTAS_PUBLICAS = {"/login"}


def _ruta_rexistrada(path: str) -> bool:
    for template in Client.page_routes.values():
        patron = re.sub(r"\{[^/]+\}", r"[^/]+", template)
        if re.fullmatch(patron, path):
            return True
    return False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        usuario_autenticado = app.storage.user.get("usuario_id")
        ruta_e_paxina_rexistrada = _ruta_rexistrada(request.url.path)
        if (
            not usuario_autenticado
            and ruta_e_paxina_rexistrada
            and request.url.path not in RUTAS_PUBLICAS
            and not request.url.path.startswith("/convite/")
            and not request.url.path.startswith("/lote/")
        ):
            return RedirectResponse("/login")
        return await call_next(request)


app.add_middleware(AuthMiddleware)

configurar_rexistro()


@app.exception_handler(404)
async def manexador_404(request: Request, exc: Exception) -> HTMLResponse:
    return pagina_erro_html("Páxina non atopada", "A ruta que buscas non existe.", 404)


@app.exception_handler(Exception)
async def manexador_500(request: Request, exc: Exception) -> HTMLResponse:
    logger.exception("Erro non controlado en {}: {}", request.url.path, exc)
    return pagina_erro_html(
        "Ocorreu un erro", "Algo saíu mal. Téntao de novo máis tarde.", 500
    )


@app.get("/fotos/{foto_id}")
def ver_foto(foto_id: int) -> Response:
    """Unha foto, só para quen pode ver a súa explotación (paso 11a)."""
    from horta.db import get_session
    from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
    from horta.services.fotos import ficheiro_da_foto
    from horta.ui.sesion import usuario_actual

    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return Response(status_code=401)
        try:
            ruta = ficheiro_da_foto(session, actor, foto_id)
        except (OperacionNonPermitidaError, PermisoDenegadoError):
            return Response(status_code=404)
    if not ruta.is_file():
        return Response(status_code=404)
    return FileResponse(ruta, headers={"Cache-Control": "private, max-age=86400"})


@app.get("/teselas/{capa}/{z}/{x}/{y}")
def ver_tesela(capa: str, z: int, x: int, y: int) -> Response:
    """Tesela do mapa (PNOA, SIGPAC, Catastro) desde a caché do ordenador ou descargada."""
    from horta.services.teselas import tesela

    if app.storage.user.get("usuario_id") is None:
        return Response(status_code=401)
    resultado = tesela(capa, z, x, y)
    if resultado is None:
        return Response(status_code=404)
    datos, mime = resultado
    return Response(datos, media_type=mime, headers={"Cache-Control": "private, max-age=604800"})


import horta.ui.admin.catalogos  # noqa: E402,F401
import horta.ui.admin.copias  # noqa: E402,F401
import horta.ui.admin.usuarios  # noqa: E402,F401
import horta.ui.pages.convite  # noqa: E402,F401
import horta.ui.pages.cue_volta  # noqa: E402,F401
import horta.ui.pages.dashboard  # noqa: E402,F401
import horta.ui.pages.horta_detalle  # noqa: E402,F401
import horta.ui.pages.login  # noqa: E402,F401
import horta.ui.pages.lote_publico  # noqa: E402,F401


def main() -> None:
    activar_actualizacions()
    ui.run(
        port=8081,
        title="Horta",
        storage_secret=segredo_sesion(),
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
