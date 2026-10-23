"""Superficies: a app garda hectáreas; o usuario escribe en m² ou ha."""

from __future__ import annotations

from nicegui import ui

M2_POR_HA = 10_000
UNIDADES_SUPERFICIE = ("m²", "ha")


def a_hectareas(valor: float | None, unidade: str) -> float | None:
    """Converte o valor escrito (en m² ou ha) a hectáreas."""
    if valor is None:
        return None
    if unidade == "m²":
        return round(float(valor) / M2_POR_HA, 6)
    return round(float(valor), 6)


def desde_hectareas(ha: float | None, unidade: str) -> float | None:
    """Converte hectáreas á unidade amosada no campo."""
    if ha is None:
        return None
    if unidade == "m²":
        return round(ha * M2_POR_HA, 2)
    return round(ha, 6)


def formatar_superficie(ha: float | None) -> str:
    """Texto para táboas: menos dunha hectárea en m², o resto en ha."""
    if ha is None:
        return ""
    if ha < 1:
        return f"{ha * M2_POR_HA:.0f} m²"
    return f"{ha:.2f} ha".replace(".", ",")


class CampoSuperficie:
    """Número + selector m²/ha. A app garda sempre hectáreas (o CUE pide ha)."""

    def __init__(self, etiqueta: str, unidade: str = "m²") -> None:
        self._unidade_anterior = unidade
        with ui.row().classes("w-full no-wrap items-end gap-2"):
            self.numero = ui.number(etiqueta, min=0).classes("col-grow")
            self.unidade = ui.select(
                list(UNIDADES_SUPERFICIE), value=unidade, label="Unidade",
                on_change=self._cambiar_unidade,
            ).classes("w-24")

    @property
    def ha(self) -> float | None:
        return a_hectareas(self.numero.value, self.unidade.value)

    def establecer(self, ha: float | None) -> None:
        unidade = "ha" if ha is not None and ha >= 1 else "m²"
        self._unidade_anterior = unidade
        self.unidade.value = unidade
        self.numero.value = desde_hectareas(ha, unidade)

    def _cambiar_unidade(self) -> None:
        ha = a_hectareas(self.numero.value, self._unidade_anterior)
        self._unidade_anterior = self.unidade.value
        self.numero.value = desde_hectareas(ha, self.unidade.value)
