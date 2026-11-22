"""Campos de formulario reutilizables."""

from __future__ import annotations

from nicegui import ui

LOCALE_GL = {
    "days": ["Domingo", "Luns", "Martes", "Mércores", "Xoves", "Venres", "Sábado"],
    "daysShort": ["Dom", "Lun", "Mar", "Mér", "Xov", "Ven", "Sáb"],
    "months": [
        "Xaneiro", "Febreiro", "Marzo", "Abril", "Maio", "Xuño",
        "Xullo", "Agosto", "Setembro", "Outubro", "Novembro", "Decembro",
    ],
    "monthsShort": [
        "Xan", "Feb", "Mar", "Abr", "Mai", "Xuñ", "Xul", "Ago", "Set", "Out", "Nov", "Dec",
    ],
    "firstDayOfWeek": 1,
}


def campo_data(etiqueta: str, valor: str = "") -> ui.input:
    """Campo de data con calendario. O valor segue sendo texto AAAA-MM-DD (ver parsear_data)."""
    with ui.input(etiqueta, value=valor).classes("w-full") as campo:
        with ui.menu().props("no-parent-event") as menu:
            calendario = ui.date(mask="YYYY-MM-DD", on_change=lambda: menu.close())
            calendario.bind_value(campo).props("minimal")
            calendario._props["locale"] = LOCALE_GL
        with campo.add_slot("append"):
            ui.icon("event").on("click", menu.open).classes("cursor-pointer")
    return campo
