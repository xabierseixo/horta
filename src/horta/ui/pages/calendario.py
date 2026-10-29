"""Calendario e mapa da explotación (paso 13): os traballos e tarefas por día, e as parcelas
no mapa. Só len o que xa hai; no mapa pódese situar unha parcela premendo nel."""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial
from typing import Any

from nicegui import events, run, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.parcelas import (
    actualizar_parcela,
    puntos_da_xeometria,
    xeometria_debuxada,
)
from horta.services.persoas import listar_persoas
from horta.services.xeo_oficial import (
    CAPAS_WMS,
    Recinto,
    SenConexion,
    completar_parcela_co_recinto,
    crear_parcela_do_recinto,
    recinto_no_punto,
    referencia_catastral_no_punto,
)
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
    debuxo = ({"draw": {"polygon": True, "marker": False, "circlemarker": False,
                        "polyline": False, "rectangle": False, "circle": False},
               "edit": False} if pode_editar else False)
    mapa = ui.leaflet(center=centro, zoom=16 if situadas else 8, draw_control=debuxo,
                      hide_drawn_items=True).classes("w-full").style("height: 60vh")
    for p, punto in situadas:
        mapa.marker(latlng=punto).run_method("bindTooltip", p.nome)
    for p in parcelas:
        forma = puntos_da_xeometria(p.geometria)
        if forma:
            mapa.generic_layer(name="polygon", args=[forma, {"color": "#2e7d32"}]
                               ).run_method("bindTooltip", p.nome)

    # Capas oficiais (as imaxes pídeas o navegador)
    capas: dict[str, Any] = {}

    def capa(clave: str, activa: bool) -> None:
        if not activa and clave in capas:
            mapa.remove_layer(capas.pop(clave))
        elif activa and clave not in capas:
            _, url, nome_capa, atribucion = CAPAS_WMS[clave]
            capas[clave] = mapa.wms_layer(url_template=url, options={
                "layers": nome_capa, "format": "image/png", "transparent": True,
                "attribution": atribucion, "maxZoom": 21})

    with ui.row().classes("items-center gap-4 q-mt-sm"):
        for clave, (nome, *_) in CAPAS_WMS.items():
            ui.checkbox(nome, on_change=lambda e, c=clave: capa(c, e.value))
    sen_situar = [p for p in parcelas if p.lat is None or p.lon is None]
    if sen_situar:
        ui.label("Sen situar no mapa: " + ", ".join(p.nome for p in sen_situar)).classes(
            "texto-suave")
    if not pode_editar:
        return

    with ui.row().classes("items-center gap-2 q-mt-sm"):
        modo = ui.select({"sigpac": "Traer o recinto SIGPAC", "catastro": "Ver a referencia "
                          "catastral", "situar": "Situar a parcela escollida"},
                         value="sigpac", label="Ao premer no mapa").classes("w-64")
        escoller = ui.select({p.id: p.nome for p in parcelas}, label="Parcela",
                             clearable=True).classes("w-64")
    ui.label("Tamén podes debuxar o contorno da parcela escollida co botón do polígono."
             ).classes("texto-suave text-caption")

    # Mentres se debuxa un contorno, os clics son os seus puntos
    debuxando = {"si": False}
    mapa.on("draw:drawstart", lambda: debuxando.update(si=True))
    mapa.on("draw:drawstop", lambda: debuxando.update(si=False))

    def gardar(cambios: dict[str, Any] | None = None, recinto: Recinto | None = None,
               nome: str | None = None) -> None:
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                return
            parcela = session.get(Parcela, escoller.value) if escoller.value else None

            def accion() -> None:
                if recinto is not None and nome is not None:
                    crear_parcela_do_recinto(session, actor_actual, horta_id, nome, recinto)
                elif parcela is None:
                    raise OperacionNonPermitidaError("Escolle primeiro a parcela")
                elif recinto is not None:
                    completar_parcela_co_recinto(session, actor_actual, parcela, recinto)
                else:
                    actualizar_parcela(session, actor_actual, parcela, **(cambios or {}))

            ok = executar_accion(session, accion)
        if ok:
            ui.navigate.reload()

    def amosar_recinto(recinto: Recinto) -> None:
        with ui.dialog() as dialogo, ui.card().style("width: min(30rem, 94vw)"):
            ui.label("Recinto SIGPAC").classes("text-h6")
            ui.label(f"Referencia: {recinto.referencia}")
            ui.label(f"Uso: {recinto.uso or '—'}")
            if recinto.puntos:
                mapa.generic_layer(name="polygon", args=[recinto.puntos,
                                                         {"color": "#f9a825"}])
            nome = ui.input("Nome da parcela nova").classes("w-full")
            with ui.row():
                ui.button("Crear parcela nova", icon="add",
                          on_click=lambda: gardar(recinto=recinto, nome=nome.value or ""))
                ui.button("Completar a parcela escollida", icon="edit",
                          on_click=lambda: gardar(recinto=recinto)).props("outline")
                ui.button("Pechar", on_click=dialogo.close).props("flat")
        dialogo.open()

    async def premer(e: events.GenericEventArguments) -> None:
        if debuxando["si"]:
            return
        punto = e.args["latlng"]
        lat, lon = round(punto["lat"], 6), round(punto["lng"], 6)
        if modo.value == "situar":
            if escoller.value is None:
                ui.notify("Escolle primeiro a parcela", type="warning")
            else:
                gardar({"lat": lat, "lon": lon})
            return
        try:
            if modo.value == "sigpac":
                recinto = await run.io_bound(recinto_no_punto, lat, lon)
                if recinto is None:
                    ui.notify("Non hai ningún recinto SIGPAC aí", type="warning")
                else:
                    amosar_recinto(recinto)
            else:
                referencia = await run.io_bound(referencia_catastral_no_punto, lat, lon)
                if referencia is None:
                    ui.notify("O Catastro non devolveu ningunha parcela aí", type="warning")
                    return
                with ui.dialog() as dialogo, ui.card():
                    ui.label(f"Referencia catastral: {referencia}").classes("text-h6")
                    with ui.row():
                        ui.button("Gardar na parcela escollida", icon="save", on_click=lambda: (
                            gardar({"referencia_catastral": referencia})))
                        ui.button("Pechar", on_click=dialogo.close).props("flat")
                dialogo.open()
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar: {erro}", type="negative")

    mapa.on("map-click", premer)

    def contorno(e: events.GenericEventArguments) -> None:
        aneis = e.args.get("layer", {}).get("_latlngs") or [[]]
        puntos = [(p["lat"], p["lng"]) for p in aneis[0]]
        try:
            geojson, hectareas, centro_p = xeometria_debuxada(puntos)
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="warning")
            return
        gardar({"geometria": geojson, "lat": centro_p[0], "lon": centro_p[1],
                "superficie": hectareas})

    mapa.on("draw:created", contorno)
