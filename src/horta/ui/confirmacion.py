from __future__ import annotations

from typing import Callable

from nicegui import ui


def confirmar_eliminacion(mensaxe: str, ao_confirmar: Callable[[], None],
                          boton: str = "Eliminar", icona: str = "delete") -> None:
    """Pide confirmación antes de executar unha acción destrutiva.

    Crea un diálogo novo cada vez que se chama (non un diálogo reutilizado),
    así que non fai falta declaralo por adiantado no corpo da páxina.
    """
    with ui.dialog() as dialog, ui.card():
        ui.label(mensaxe)
        with ui.row().classes("q-mt-sm justify-end w-full"):
            ui.button("Cancelar", on_click=dialog.close).props("flat")

            def confirmado() -> None:
                dialog.close()
                ao_confirmar()

            ui.button(boton, icon=icona, on_click=confirmado).props("color=negative")
    dialog.open()
