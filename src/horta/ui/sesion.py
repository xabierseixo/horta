from __future__ import annotations

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.idiomas import _
from horta.models.usuario import Usuario
from horta.services.auth import obter_usuario_activo


def usuario_actual(session: Session) -> Usuario | None:
    """Usuario da sesión actual, ou None se non hai sesión ou xa non é válida.

    Revalida en cada chamada que o usuario segue existindo e activo, de xeito
    que desactivar un usuario revoga tamén as sesións que xa tiña abertas.
    """
    usuario_id = app.storage.user.get("usuario_id")
    if usuario_id is None:
        return None
    return obter_usuario_activo(session, usuario_id)


def pechar_sesion() -> None:
    """Borra a sesión do navegador e leva á páxina de login."""
    app.storage.user.clear()
    ui.navigate.to("/login")


def boton_pechar_sesion() -> None:
    ui.button(_("Pechar sesión"), icon="logout", on_click=pechar_sesion).props("flat")
