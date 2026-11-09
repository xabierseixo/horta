"""Páxina pública dun lote (xemelgo dixital, paso 17): sen sesión, co enderezo secreto. Para
quen merca: de onde vén e que se lle fixo; nunca a quen se vendeu."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.services.trazabilidade import trazabilidade_publica
from horta.ui.tema import aplicar_tema


@ui.page("/lote/{token}")
def paxina_lote(token: str) -> None:
    aplicar_tema()
    with get_session() as session:
        resultado = trazabilidade_publica(session, token)
    with ui.column().classes("w-full q-pa-md").style("max-width: 44rem; margin: auto"):
        if resultado is None:
            ui.label(_("Este lote non existe ou xa non está publicado.")).classes("text-h6")
            return
        traz, explotacion = resultado
        ui.label(traz.lote.produto).classes("text-h5 text-weight-bold")
        ui.label(
            _("Lote {codigo} · {explotacion}").format(
                codigo=traz.lote.codigo, explotacion=explotacion
            )
        ).classes("texto-suave")
        for titulo, lineas in (
            (_("De onde vén"), traz.orixe),
            (_("Que se lle fixo"), traz.fixose),
            (_("Preparación"), traz.dentro),
        ):
            ui.label(titulo).classes("text-subtitle1 text-weight-bold q-mt-md")
            if not lineas:
                ui.label(_("Nada apuntado.")).classes("texto-suave")
            for linea in lineas:
                data = f"{linea.data:%d/%m/%Y} · " if linea.data else ""
                ui.label(f"{data}{linea.texto}")
        ui.label(
            _("Información do caderno da explotación, apuntada pola propia explotación.")
        ).classes("texto-suave text-caption q-mt-lg")
