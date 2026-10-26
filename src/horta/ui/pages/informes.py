"""Informes: o que sae do traballo apuntado. Hoxe, o caderno de explotación e o que lle falta."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.faltas_caderno import faltas_caderno
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.layout import url_seccion
from horta.ui.sesion import pechar_sesion, usuario_actual

_SECCION_DA_FALTA = {"Tratamentos": "tratamentos", "Abonados": "fertilizacion",
                     "Regas": "rega", "Labores": "labores"}


def seccion_informes(horta_id: int, uso_profesional: bool) -> None:
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md"):
        ui.label("Caderno de explotación").classes("text-subtitle1 text-weight-bold")
        ui.label("Modelo da Xunta en Excel, co período que escollas. Sae do que está apuntado."
                 ).classes("texto-suave")
        boton_caderno(horta_id)
    if not uso_profesional:
        ui.label("Explotación non profesional: o caderno non é obrigatorio, pero podes "
                 "descargalo se che serve.").classes("texto-suave q-mt-md")
        return
    inicio_ano = date(date.today().year, 1, 1)
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        faltas = faltas_caderno(session, actor, horta_id, desde=inicio_ano)
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-mt-md"):
        ui.label(f"Que lle falta ao caderno de {inicio_ano.year}").classes(
            "text-subtitle1 text-weight-bold")
        if not faltas:
            ui.label("Nada: o apuntado ten todo o que pide o caderno.").classes("etiqueta-ok")
            return
        ui.label("Non impide descargalo: complétao cando poidas.").classes("texto-suave")
        for falta in faltas:
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning").classes("text-warning")
                ui.label(f"{falta.traballo}: {falta.cantos} sen {falta.dato}")
                ui.link("Ver", url_seccion(horta_id, _SECCION_DA_FALTA[falta.traballo]))
