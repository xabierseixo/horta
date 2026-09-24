from __future__ import annotations

import os
import re

from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import Client, app, ui
from starlette.middleware.base import BaseHTTPMiddleware

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
        ):
            return RedirectResponse("/login")
        return await call_next(request)


app.add_middleware(AuthMiddleware)

import horta.ui.pages.login  # noqa: E402,F401
import horta.ui.pages.dashboard  # noqa: E402,F401
import horta.ui.pages.horta_detalle  # noqa: E402,F401
import horta.ui.admin.usuarios  # noqa: E402,F401


def main() -> None:
    ui.run(
        port=8081,
        title="Horta",
        storage_secret=os.environ.get("HORTA_STORAGE_SECRET", "dev-secret-cambiar-en-produccion"),
        reload=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
