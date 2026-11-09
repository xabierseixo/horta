"""Campos de formulario reutilizables."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from horta.idiomas import N_, _
from horta.ui.numeros import texto_data

LOCALE_GL: dict[str, Any] = {
    "days": [
        N_("Domingo"), N_("Luns"), N_("Martes"), N_("Mércores"),
        N_("Xoves"), N_("Venres"), N_("Sábado"),
    ],
    "daysShort": [
        N_("Dom"), N_("Lun"), N_("Mar"), N_("Mér"),
        N_("Xov"), N_("Ven"), N_("Sáb"),
    ],
    "months": [
        N_("Xaneiro"), N_("Febreiro"), N_("Marzo"), N_("Abril"),
        N_("Maio"), N_("Xuño"), N_("Xullo"), N_("Agosto"),
        N_("Setembro"), N_("Outubro"), N_("Novembro"), N_("Decembro"),
    ],
    "monthsShort": [
        N_("Xan"), N_("Feb"), N_("Mar"), N_("Abr"),
        N_("Mai"), N_("Xuñ"), N_("Xul"), N_("Ago"),
        N_("Set"), N_("Out"), N_("Nov"), N_("Dec"),
    ],
    "firstDayOfWeek": 1,
}


def obter_locale() -> dict[str, object]:
    """Devolve a configuración rexional para o calendario no idioma actual."""
    return {
        "days": [_(d) for d in LOCALE_GL["days"]],
        "daysShort": [_(d) for d in LOCALE_GL["daysShort"]],
        "months": [_(m) for m in LOCALE_GL["months"]],
        "monthsShort": [_(m) for m in LOCALE_GL["monthsShort"]],
        "firstDayOfWeek": LOCALE_GL["firstDayOfWeek"],
    }


def campo_data(etiqueta: str, valor: str = "") -> ui.input:
    """Campo de data con calendario. O valor é texto DD/MM/AAAA (ver parsear_data); se se
    lle pon AAAA-MM-DD, pásao a DD/MM/AAAA (X6)."""
    with ui.input(_(etiqueta), value=texto_data(valor)).classes("w-full") as campo:
        with ui.menu().props("no-parent-event") as menu:
            calendario = ui.date(mask="DD/MM/YYYY", on_change=lambda: menu.close())
            calendario.bind_value(campo).props("minimal")
            calendario._props["locale"] = obter_locale()
        with campo.add_slot("append"):
            ui.icon("event").on("click", menu.open).classes("cursor-pointer")

    def normalizar() -> None:
        texto = texto_data(campo.value)
        if texto != campo.value:
            campo.value = texto

    campo.on_value_change(normalizar)
    return campo
