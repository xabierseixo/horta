"""Páxinas de textos legais e aceptación da política de privacidade."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.services.legal import aceptar_politica, texto_legal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.tema import aplicar_tema


@ui.page("/legal/aviso")
def paxina_aviso_legal() -> None:
    aplicar_tema()
    with get_session() as session:
        contido = texto_legal(session, "aviso")
    with ui.column().classes("w-full q-pa-md").style("max-width: 44rem; margin: auto"):
        ui.markdown(contido)


@ui.page("/legal/privacidade")
def paxina_politica_privacidade() -> None:
    aplicar_tema()
    with get_session() as session:
        contido = texto_legal(session, "privacidade")
    with ui.column().classes("w-full q-pa-md").style("max-width: 44rem; margin: auto"):
        ui.markdown(contido)


@ui.page("/legal/aceptar")
def paxina_aceptar_politica() -> None:
    aplicar_tema()
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return

    def ao_aceptar() -> None:
        with get_session() as session:
            actor_db = usuario_actual(session)
            if actor_db is None:
                pechar_sesion()
                return
            aceptar_politica(session, actor_db)
        ui.navigate.to("/")

    with ui.column().classes("w-full q-pa-md").style("max-width: 44rem; margin: auto"):
        with ui.card().classes("w-full q-pa-lg gap-4"):
            ui.label("Antes de continuar").classes("text-h5 text-weight-bold")
            ui.label(
                "Para usar AgroXest360 tes que ler e aceptar a política de privacidade e o "
                "aviso legal."
            )
            with ui.row().classes("gap-4"):
                ui.link("Aviso legal", "/legal/aviso", new_tab=True)
                ui.link("Política de privacidade", "/legal/privacidade", new_tab=True)
            caixa = ui.checkbox("Lin e acepto a política de privacidade e o aviso legal")
            with ui.row().classes("w-full items-center justify-between q-mt-md"):
                ui.button("Saír", on_click=pechar_sesion).props("flat")
                boton = ui.button("Aceptar e continuar", on_click=ao_aceptar)
                boton.bind_enabled_from(caixa, "value")
