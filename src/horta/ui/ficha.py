"""Compoñente común para a ficha dun recurso (datos, historial e fotos)."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui


def abrir_ficha(
    titulo: str,
    datos: list[tuple[str, str]],
    historial: list[str],
    fotos: Callable[[], None] | None = None,
) -> None:
    """Abre o diálogo coa ficha dun recurso: título, datos, historial e fotos."""
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        ui.label(titulo).classes("text-h6")

        if datos:
            with ui.element("div").style(
                "display:grid; grid-template-columns:auto 1fr; gap:2px 12px"
            ):
                for etiqueta, valor in datos:
                    ui.label(etiqueta).classes("texto-suave")
                    ui.label(valor)

        ui.label("Historial").classes("text-weight-medium q-mt-sm")
        with ui.column().classes("gap-0"):
            if historial:
                for lina in historial:
                    ui.label(lina).classes("texto-suave")
            else:
                ui.label("Aínda non hai traballos").classes("texto-suave")

        if fotos is not None:
            ui.button("Fotos", icon="photo_camera", on_click=fotos).props("outline").classes(
                "w-full q-mt-sm"
            )

        ui.button("Pechar", on_click=dialogo.close).props("flat").classes("w-full q-mt-sm")

    dialogo.open()
