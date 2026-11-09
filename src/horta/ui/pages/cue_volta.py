"""Volta da Xunta tras identificarse (comunicacionProductor): a URL de volta que se rexistra
no trámite MR407B é https://<dominio>/cue/volta (Anexo VI, Anexo 8)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.services.conexion_xeaga import desconectar, recibir_token
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import titular_da_horta
from horta.ui.layout import url_seccion
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/cue/volta")
def cue_volta_page(peticion: str = "", token: str = "") -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            horta_id, recibido = recibir_token(peticion, token, actor.id)
        except OperacionNonPermitidaError as erro:
            ui.label(str(erro)).classes("text-negative q-pa-md")
            return
        titular = titular_da_horta(session, horta_id)
        if titular is None or not titular.nif or titular.nif != recibido.nif:
            desconectar(actor.id, horta_id)
            ui.label(
                _(
                    "Quen se identificou na Xunta non é a persoa titular desta explotación "
                    "(o NIF non coincide co da ficha da persoa titular)."
                )
            ).classes("text-negative q-pa-md")
            ui.link(_("Volver aos informes"), url_seccion(horta_id, "informes"))
            return
    ui.navigate.to(url_seccion(horta_id, "informes"))
