"""Botón «Descargar o caderno»: Excel co modelo oficial da Xunta para o período escollido."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual


def boton_caderno(horta_id: int) -> None:
    hoxe = date.today()
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Descargar o caderno de explotación").classes("text-h6")
        ui.label("Excel co modelo oficial da Xunta. Podes descargalo cando queiras, "
                 "para o período que necesites.").classes("text-caption")
        desde = campo_data("Desde", date(hoxe.year, 1, 1).isoformat())
        ata = campo_data("Ata", hoxe.isoformat())

        def descargar() -> None:
            inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            if inicio is None or fin is None:
                ui.notify("Indica as dúas datas", type="warning")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                try:
                    datos = xerar_caderno(session, actor, horta_id, inicio, fin)
                except OperacionNonPermitidaError as erro:
                    ui.notify(str(erro), type="negative")
                    return
            ui.download.content(datos, f"caderno-{inicio:%Y%m%d}-{fin:%Y%m%d}.xlsx")
            dialogo.close()

        with ui.row():
            ui.button("Descargar", icon="download", on_click=descargar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
    ui.button("Descargar o caderno", icon="download", on_click=dialogo.open).props("outline")
