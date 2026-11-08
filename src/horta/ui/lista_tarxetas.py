"""Compoñente común para listas en tarxetas no móbil."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from horta.ui.ficha import abrir_ficha


def lista_tarxetas(
    elementos: list[tuple[int, str, str]],
    ao_tocar: Callable[[int], None],
    baleiro: str = "Aínda non hai nada apuntado",
) -> None:
    """Debuxa unha lista de tarxetas para pantallas móbiles."""
    if not elementos:
        ui.label(baleiro).classes("so-movil texto-suave")
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


def datos_da_fila(
    columnas: list[dict[str, Any]],
    fila: dict[str, Any],
) -> list[tuple[str, str]]:
    """Devolve etiqueta e valor para cada columna non baleira da fila."""
    resultado: list[tuple[str, str]] = []
    for col in columnas:
        campo = col.get("field")
        if not campo:
            continue
        valor = fila.get(campo)
        if valor is None or valor == "":
            continue
        etiqueta = str(col.get("label", campo))
        resultado.append((etiqueta, str(valor)))
    return resultado


def tarxetas_da_taboa(
    taboa: ui.table,
    titulo: str,
    detalle: list[str],
    accions: list[tuple[str, str, Callable[[], None]]],
) -> ui.refreshable:
    """Debuxa tarxetas para as filas da táboa no móbil con apertura de ficha."""

    @ui.refreshable
    def debuxar() -> None:
        filas = list(taboa.rows or [])
        elementos = [
            (
                idx,
                str(fila[titulo]),
                " · ".join(
                    str(fila[c])
                    for c in detalle
                    if fila.get(c) is not None and fila.get(c) != ""
                ),
            )
            for idx, fila in enumerate(filas)
        ]

        def ao_tocar(idx: int) -> None:
            fila = filas[idx]
            taboa.selected = [fila]
            abrir_ficha(
                str(fila[titulo]),
                datos_da_fila(taboa.columns, fila),
                None,
                accions=accions or None,
            )

        baleiro = taboa.props.get("no-data-label") or "Aínda non hai nada apuntado"
        lista_tarxetas(elementos, ao_tocar=ao_tocar, baleiro=str(baleiro))

    debuxar()
    return debuxar
