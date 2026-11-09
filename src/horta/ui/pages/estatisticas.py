"""Sección Estatísticas (paso 15): gráficas (ui.echart) do que xa está apuntado."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.services.estatisticas import (
    auga_por_mes,
    cartos_por_mes,
    clases_do_ano,
    enerxia_por_mes,
    producion_por_ano,
)
from horta.ui.numeros import euros, formatar_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_MESES = [
    N_("xan"),
    N_("feb"),
    N_("mar"),
    N_("abr"),
    N_("mai"),
    N_("xuñ"),
    N_("xul"),
    N_("ago"),
    N_("set"),
    N_("out"),
    N_("nov"),
    N_("dec"),
]


def _grafica(titulo: str, opcions: dict) -> None:
    with ui.column().classes("tarxeta w-full gap-1 q-pa-md"):
        ui.label(_(titulo)).classes("text-subtitle1 text-weight-bold")
        ui.echart({
            "tooltip": {"trigger": "axis"},
            "legend": {"top": 0},
            "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
            **opcions,
        }).classes("w-full").style("height: 320px")


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
            enerxia = enerxia_por_mes(session, actor, horta_id, ano)
            cartos = cartos_por_mes(session, actor, horta_id, ano) if pode_editar else None
        anos = [str(a) for a in range(ano - 4, ano + 1)]
        meses_etiquetas = [_(m) for m in _MESES]
        if producion:
            _grafica(
                _("Produción (kg, ou a súa unidade)"),
                {
                    "xAxis": {"type": "category", "data": anos},
                    "yAxis": {"type": "value"},
                    "series": [
                        {
                            "name": nome,
                            "type": "bar",
                            "data": [valores.get(int(a), 0) for a in anos],
                        }
                        for nome, valores in sorted(producion.items())
                    ],
                },
            )
        else:
            ui.label(_("Aínda non hai colleitas nin produción apuntadas.")).classes("texto-suave")
        if clases:
            produtos = sorted(clases)
            todas = sorted({c for v in clases.values() for c in v})
            _grafica(
                _("Clasificación e refugo en {ano}").format(ano=ano),
                {
                    "xAxis": {"type": "category", "data": produtos},
                    "yAxis": {"type": "value"},
                    "series": [
                        {
                            "name": c,
                            "type": "bar",
                            "stack": "total",
                            "data": [clases[p].get(c, 0) for p in produtos],
                        }
                        for c in todas
                    ],
                },
            )
        _grafica(
            _("Choiva e rega en {ano}").format(ano=ano),
            {
                "xAxis": {"type": "category", "data": meses_etiquetas},
                "yAxis": [{"type": "value", "name": "l/m²"}, {"type": "value", "name": "m³"}],
                "series": [
                    {"name": _("Choiva (l/m²)"), "type": "bar", "data": auga.choiva},
                    {"name": _("Rega (m³)"), "type": "line", "yAxisIndex": 1, "data": auga.rega},
                ],
            },
        )
        if enerxia.cantidades or any(enerxia.importe):
            with ui.column().classes("tarxeta w-full gap-1 q-pa-md"):
                ui.label(_("Enerxía")).classes("text-subtitle1 text-weight-bold")
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "legend": {"top": 0},
                    "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
                    "xAxis": {"type": "category", "data": meses_etiquetas},
                    "yAxis": {"type": "value", "name": "€"},
                    "series": [
                        {"name": _("Importe (€)"), "type": "bar", "data": enerxia.importe}
                    ],
                }).classes("w-full").style("height: 320px")
                filas = [
                    {
                        "tipo": tipo,
                        "total": f"{formatar_decimal(round(sum(meses), 2))} {unidade}",
                    }
                    for (tipo, unidade), meses in enerxia.cantidades.items()
                ]
                filas.append({
                    "tipo": _("Gasto total"),
                    "total": euros(round(sum(enerxia.importe), 2)),
                })
                ui.table(
                    columns=[
                        {"name": "tipo", "label": _("Tipo"), "field": "tipo", "align": "left"},
                        {
                            "name": "total",
                            "label": _("Total do ano"),
                            "field": "total",
                            "align": "right",
                        },
                    ],
                    rows=filas,
                ).classes("w-full taboa").props(f"flat bordered dense {TEXTOS_TABOA}")
        else:
            with ui.column().classes("tarxeta w-full gap-1 q-pa-md"):
                ui.label(_("Enerxía")).classes("text-subtitle1 text-weight-bold")
                ui.label(
                    _(
                        "Aínda non hai compras de enerxía. "
                        "Apúntaas en Produtos como un produto de tipo Enerxía."
                    )
                ).classes("texto-suave")
        if cartos is not None:
            _grafica(
                _("Ingresos e gastos en {ano} (€)").format(ano=ano),
                {
                    "xAxis": {"type": "category", "data": meses_etiquetas},
                    "yAxis": {"type": "value"},
                    "series": [
                        {"name": _("Ingresos"), "type": "bar", "data": cartos[0]},
                        {"name": _("Gastos"), "type": "bar", "data": cartos[1]},
                    ],
                },
            )

    ui.select(
        list(range(date.today().year, date.today().year - 10, -1)),
        label=_("Ano"),
        value=estado["ano"],
        on_change=lambda e: (estado.update(ano=e.value), graficas.refresh()),
    )
    graficas()
