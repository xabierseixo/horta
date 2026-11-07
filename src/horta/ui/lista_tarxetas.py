"""Compoñente común para listas en tarxetas no móbil."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui


def lista_tarxetas(
    elementos: list[tuple[int, str, str]],
    ao_tocar: Callable[[int], None],
) -> None:
    """Debuxa unha lista de tarxetas para pantallas móbiles."""
    if not elementos:
        return

    with ui.column().classes("so-movil w-full gap-2"):
        for id_elem, titulo, detalle in elementos:
            with (
                ui.card()
                .classes("w-full cursor-pointer")
                .on("click", lambda _e=None, i=id_elem: ao_tocar(i))
            ):
                with ui.row().classes("w-full items-center justify-between no-wrap"):
                    with ui.column().classes("gap-0"):
                        ui.label(titulo).classes("font-bold")
                        if detalle:
                            ui.label(detalle).classes("texto-suave")
                    ui.label("›").classes("text-xl texto-suave")
