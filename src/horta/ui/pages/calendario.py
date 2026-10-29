"""Calendario e mapa da explotación (paso 13): os traballos e tarefas por día, e as parcelas
no mapa. Só len o que xa hai; no mapa pódese situar unha parcela premendo nel."""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial

from nicegui import events, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.services.diario import listar_traballos
from horta.services.parcelas import actualizar_parcela
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.campos import LOCALE_GL
from horta.ui.pages.diario import Formularios, tarxeta
from horta.ui.sesion import pechar_sesion, usuario_actual

# Centro de Galicia, se a explotación non ten coordenadas
_GALICIA = (42.75, -8.0)


def seccion_calendario(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        traballos = listar_traballos(session, actor, horta_id,
                                     desde=date.today() - timedelta(days=365))
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}
    formularios = Formularios(horta_id) if pode_editar else None
    por_dia: dict[str, list] = {}
    for t in traballos:
        if t.data is not None:
            por_dia.setdefault(t.data.isoformat(), []).append(t)

    calendario = ui.date(value=date.today().isoformat(), mask="YYYY-MM-DD")
    calendario._props["events"] = [d.replace("-", "/") for d in por_dia]
    calendario._props["locale"] = LOCALE_GL

    @ui.refreshable
    def do_dia() -> None:
        dia = calendario.value
        if not dia:
            return
        ui.label(f"{date.fromisoformat(dia):%d/%m/%Y}").classes(
            "text-subtitle1 text-weight-bold q-mt-md")
        lista = por_dia.get(dia, [])
        if not lista:
            ui.label("Nada apuntado nin por facer este día.").classes("texto-suave")
        with ui.column().classes("w-full gap-2"):
            for t in lista:
                tarxeta(t, partial(formularios.editar, t) if formularios else lambda: None,
                        persoas, horta_id, pode_editar, 0)

    calendario.on_value_change(do_dia.refresh)
    do_dia()


def seccion_mapa(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        horta = session.get(Horta, horta_id)
        parcelas = list(session.query(Parcela).filter_by(horta_id=horta_id))
    situadas = [(p, (p.lat, p.lon)) for p in parcelas if p.lat is not None and p.lon is not None]
    centro = (situadas[0][1] if situadas
              else (horta.lat, horta.lon) if horta and horta.lat and horta.lon else _GALICIA)
    mapa = ui.leaflet(center=centro, zoom=15 if situadas else 8).classes("w-full").style(
        "height: 60vh")
    for p, punto in situadas:
        mapa.marker(latlng=punto).run_method("bindTooltip", p.nome)
    sen_situar = [p for p in parcelas if p.lat is None or p.lon is None]
    if sen_situar:
        ui.label("Sen situar no mapa: " + ", ".join(p.nome for p in sen_situar)).classes(
            "texto-suave q-mt-sm")
    if not pode_editar or not parcelas:
        return
    with ui.row().classes("items-center gap-2 q-mt-sm"):
        escoller = ui.select({p.id: p.nome for p in parcelas}, label="Situar a parcela"
                             ).classes("w-64")
        ui.label("e preme no mapa onde está.").classes("texto-suave")

    def situar(e: events.GenericEventArguments) -> None:
        if escoller.value is None:
            return
        punto = e.args["latlng"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            parcela = session.get(Parcela, escoller.value)
            if actor_actual is None or parcela is None:
                return
            ok = executar_accion(session, lambda: actualizar_parcela(
                session, actor_actual, parcela, lat=round(punto["lat"], 6),
                lon=round(punto["lng"], 6)))
        if ok:
            ui.navigate.reload()

    mapa.on("map-click", situar)
