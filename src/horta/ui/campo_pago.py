"""Cobrada ou pagada, e cando (paso 10, cartos): unha caixa e a data, que se ve só ao
marcala. Sen data, cóntase a data da operación."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.idiomas import _
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data


class CampoPago:
    def __init__(self, etiqueta: str) -> None:
        with ui.row().classes("w-full no-wrap items-center"):
            self.feito = ui.checkbox(_(etiqueta), value=True)
            with ui.element("div").classes("col") as self._bloque:
                self.data = campo_data(_("Cando (baleiro: o mesmo día)"))
        self.feito.on_value_change(lambda: self._bloque.set_visibility(self.feito.value))

    def valor(self, data_operacion: date | None) -> date | None:
        if not self.feito.value:
            return None
        return parsear_data(self.data.value) or data_operacion

    def poñer(self, data_pago: date | None, nova: bool) -> None:
        """Nunha operación nova, marcada; nunha gardada, como estea."""
        self.feito.value = nova or data_pago is not None
        self.data.value = data_pago.isoformat() if data_pago else ""
        self._bloque.set_visibility(self.feito.value)
