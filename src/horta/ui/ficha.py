"""Compoñente común para a ficha dun recurso (datos, historial e fotos)."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.idiomas import _


def abrir_ficha(
    titulo: str,
    datos: list[tuple[str, str]],
    historial: list[str] | None,
    fotos: Callable[[], None] | None = None,
    accions: list[tuple[str, str, Callable[[], None]]] | None = None,
) -> None:
    """Abre o diálogo coa ficha dun recurso: título, datos, historial e fotos."""
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        ui.label(_(titulo)).classes("text-h6")

        if datos:
            with ui.element("div").style(
                "display:grid; grid-template-columns:auto 1fr; gap:2px 12px"
            ):
                for etiqueta, valor in datos:
                    ui.label(_(etiqueta)).classes("texto-suave")
                    ui.label(valor)

        if historial is not None:
            ui.label(_("Historial")).classes("text-weight-medium q-mt-sm")
            with ui.column().classes("gap-0"):
                if historial:
                    for lina in historial:
                        ui.label(lina).classes("texto-suave")
                else:
                    ui.label(_("Aínda non hai traballos")).classes("texto-suave")

        if fotos is not None:
            ui.button(_("Fotos"), icon="photo_camera", on_click=fotos).props("outline").classes(
                "w-full q-mt-sm"
            )

        if accions:
            for texto, icona, fn in accions:
                def manexador(f: Callable[[], None]) -> Callable[[], None]:
                    def accion() -> None:
                        dialogo.close()
                        f()

                    return accion

                ui.button(_(texto), icon=icona, on_click=manexador(fn)).props("outline").classes(
                    "w-full q-mt-sm"
                )

        ui.button(_("Pechar"), on_click=dialogo.close).props("flat").classes("w-full q-mt-sm")

    dialogo.open()
