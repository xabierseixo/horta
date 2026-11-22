"""Sección Estatísticas (paso 15): gráficas (ui.echart) do que xa está apuntado."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.estatisticas import (
    auga_por_mes,
    cartos_por_mes,
    clases_do_ano,
    producion_por_ano,
)
from horta.ui.sesion import pechar_sesion, usuario_actual

_MESES = ["xan", "feb", "mar", "abr", "mai", "xuñ", "xul", "ago", "set", "out", "nov", "dec"]


def _grafica(titulo: str, opcions: dict) -> None:
    with ui.column().classes("tarxeta w-full gap-1 q-pa-md"):
        ui.label(titulo).classes("text-subtitle1 text-weight-bold")
        ui.echart({"tooltip": {"trigger": "axis"}, "legend": {"top": 0},
                   "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
                   **opcions}).classes("w-full").style("height: 320px")


def seccion_estatisticas(horta_id: int, pode_editar: bool) -> None:
    estado = {"ano": date.today().year}

    @ui.refreshable
    def graficas() -> None:
        ano = estado["ano"]
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            producion = producion_por_ano(session, actor, horta_id, ano)
            clases = clases_do_ano(session, actor, horta_id, ano)
            auga = auga_por_mes(session, actor, horta_id, ano)
            cartos = cartos_por_mes(session, actor, horta_id, ano) if pode_editar else None
        anos = [str(a) for a in range(ano - 4, ano + 1)]
        if producion:
            _grafica("Produción (kg, ou a súa unidade)", {
                "xAxis": {"type": "category", "data": anos}, "yAxis": {"type": "value"},
                "series": [{"name": nome, "type": "bar",
                            "data": [valores.get(int(a), 0) for a in anos]}
                           for nome, valores in sorted(producion.items())]})
        else:
            ui.label("Aínda non hai colleitas nin produción apuntadas.").classes("texto-suave")
        if clases:
            produtos = sorted(clases)
            todas = sorted({c for v in clases.values() for c in v})
            _grafica(f"Clasificación e refugo en {ano}", {
                "xAxis": {"type": "category", "data": produtos}, "yAxis": {"type": "value"},
                "series": [{"name": c, "type": "bar", "stack": "total",
                            "data": [clases[p].get(c, 0) for p in produtos]} for c in todas]})
        _grafica(f"Choiva e rega en {ano}", {
            "xAxis": {"type": "category", "data": _MESES},
            "yAxis": [{"type": "value", "name": "l/m²"}, {"type": "value", "name": "m³"}],
            "series": [{"name": "Choiva (l/m²)", "type": "bar", "data": auga.choiva},
                       {"name": "Rega (m³)", "type": "line", "yAxisIndex": 1,
                        "data": auga.rega}]})
        if cartos is not None:
            _grafica(f"Ingresos e gastos en {ano} (€)", {
                "xAxis": {"type": "category", "data": _MESES}, "yAxis": {"type": "value"},
                "series": [{"name": "Ingresos", "type": "bar", "data": cartos[0]},
                           {"name": "Gastos", "type": "bar", "data": cartos[1]}]})

    ui.select(list(range(date.today().year, date.today().year - 10, -1)), label="Ano",
              value=estado["ano"],
              on_change=lambda e: (estado.update(ano=e.value), graficas.refresh()))
    graficas()
