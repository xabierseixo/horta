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
from horta.models.zona import ParcelaZona
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
    PNOA_TESELAS,
    ParcelaCatastral,
    Recinto,
    SenConexion,
    completar_parcela_co_catastro,
    completar_parcela_co_recinto,
    crear_parcela_do_catastro,
    crear_parcela_do_recinto,
    parcela_catastral_no_punto,
    recinto_no_punto,
)
from horta.services.zonas import (
    TIPOS_ZONA,
    aviso_superficie,
    borrar_zona,
    crear_zona,
    dividir_en_bancais,
    listar_zonas,
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
        zonas = {p.id: listar_zonas(session, actor, p) for p in parcelas}
        avisos = [a for p in parcelas if (a := aviso_superficie(session, p))]
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
        for z in zonas[p.id]:
            forma_z = puntos_da_xeometria(z.geometria)
            if forma_z:
                mapa.generic_layer(name="polygon", args=[forma_z, {
                    "color": "#ef6c00", "weight": 1, "dashArray": "4"}]).run_method(
                    "bindTooltip", f"{p.nome} · {z.nome}")

    # Capas oficiais (as imaxes pídeas o navegador)
    capas: dict[str, Any] = {}

    def capa(clave: str, activa: bool) -> None:
        if not activa and clave in capas:
            mapa.remove_layer(capas.pop(clave))
        elif activa and clave not in capas:
            if clave == "pnoa":
                # Debaixo das capas SIGPAC e Catastro
                capas[clave] = mapa.tile_layer(url_template=PNOA_TESELAS, options={
                    "attribution": "PNOA © IGN", "maxZoom": 20, "zIndex": 1})
                return
            _, url, nome_capa, atribucion = CAPAS_WMS[clave]
            capas[clave] = mapa.wms_layer(url_template=url, options={
                "layers": nome_capa, "format": "image/png", "transparent": True,
                "attribution": atribucion, "maxZoom": 21, "zIndex": 10})

    with ui.row().classes("items-center gap-4 q-mt-sm"):
        ui.checkbox("Ortofoto (PNOA)", on_change=lambda e: capa("pnoa", e.value))
        for clave, (nome, *_) in CAPAS_WMS.items():
            ui.checkbox(nome, on_change=lambda e, c=clave: capa(c, e.value))
    sen_situar = [p for p in parcelas if p.lat is None or p.lon is None]
    if sen_situar:
        ui.label("Sen situar no mapa: " + ", ".join(p.nome for p in sen_situar)).classes(
            "texto-suave")
    if not pode_editar:
        return

    with ui.row().classes("items-center gap-2 q-mt-sm"):
        modo = ui.select({"nada": "Só mirar", "sigpac": "Traer o recinto SIGPAC",
                          "catastro": "Traer a parcela do Catastro",
                          "situar": "Situar a parcela escollida"},
                         value="nada", label="Ao premer no mapa").classes("w-64")
        escoller = ui.select({p.id: p.nome for p in parcelas}, label="Parcela",
                             clearable=True).classes("w-64")
    with ui.dialog() as dividir_dialogo, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Dividir a parcela escollida en bancais iguais").classes("text-h6")
        cantos = ui.number("Cantos bancais", value=4, min=1, step=1).classes("w-full")
        orientacion = ui.number("Dirección dos bancais (graos desde o norte: 0 = norte–sur, "
                                "90 = leste–oeste)", value=0, min=0, max=180).classes("w-full")
        paso = ui.number("Paso entre bancais (m)", value=0.5, min=0, step=0.1).classes(
            "w-full")
        base = ui.input("Nome", value="Bancal").classes("w-full")

        def dividir() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                parcela = session.get(Parcela, escoller.value) if escoller.value else None
                if actor_actual is None:
                    return

                def accion() -> None:
                    if parcela is None:
                        raise OperacionNonPermitidaError("Escolle primeiro a parcela")
                    dividir_en_bancais(session, actor_actual, parcela, int(cantos.value or 0),
                                       float(orientacion.value or 0), float(paso.value or 0),
                                       base.value or "")

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Dividir", icon="view_week", on_click=dividir)
            ui.button("Cancelar", on_click=dividir_dialogo.close).props("flat")

    with ui.row().classes("items-center gap-2"):
        destino = ui.select({"contorno": "O contorno da parcela", "zona": "Unha zona dentro "
                             "dela"}, value="contorno", label="O que debuxas co polígono é"
                            ).classes("w-64")
        tipo_zona = ui.select(TIPOS_ZONA, value="bancal", label="Tipo de zona").classes("w-48")
        nome_zona = ui.input("Nome da zona").classes("w-48")
        ui.button("Dividir en bancais", icon="view_week",
                  on_click=lambda: dividir_dialogo.open()).props("outline")
    tipo_zona.bind_visibility_from(destino, "value", value="zona")
    nome_zona.bind_visibility_from(destino, "value", value="zona")
    for aviso in avisos:
        ui.label(aviso).classes("etiqueta-aviso")

    # As zonas de cada parcela, para borralas
    with ui.expansion("Zonas das parcelas", icon="grid_view").classes("w-full q-mt-sm"):
        for p in parcelas:
            for z in zonas[p.id]:
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"{p.nome} · {z.nome} ({TIPOS_ZONA[z.tipo]}): "
                             f"{(z.superficie or 0) * 10000:.0f} m²")
                    ui.button(icon="delete", on_click=lambda z=z: borrar(z.id)).props(
                        "flat dense round size=sm color=negative")
        if not any(zonas.values()):
            ui.label("Aínda non hai zonas.").classes("texto-suave")

    def borrar(zona_id: int) -> None:
        with get_session() as session:
            actor_actual = usuario_actual(session)
            zona = session.get(ParcelaZona, zona_id)
            if actor_actual is None or zona is None:
                return
            ok = executar_accion(session, lambda: borrar_zona(session, actor_actual, zona))
        if ok:
            ui.navigate.reload()

    # Mentres se debuxa un contorno, os clics son os seus puntos
    debuxando = {"si": False}
    mapa.on("draw:drawstart", lambda: debuxando.update(si=True))
    mapa.on("draw:drawstop", lambda: debuxando.update(si=False))

    def gardar(cambios: dict[str, Any] | None = None, recinto: Recinto | None = None,
               nome: str | None = None, catastral: ParcelaCatastral | None = None) -> None:
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                return
            parcela = session.get(Parcela, escoller.value) if escoller.value else None

            def accion() -> None:
                if recinto is not None and nome is not None:
                    crear_parcela_do_recinto(session, actor_actual, horta_id, nome, recinto)
                elif catastral is not None and nome is not None:
                    crear_parcela_do_catastro(session, actor_actual, horta_id, nome, catastral)
                elif parcela is None:
                    raise OperacionNonPermitidaError("Escolle primeiro a parcela")
                elif recinto is not None:
                    completar_parcela_co_recinto(session, actor_actual, parcela, recinto)
                elif catastral is not None:
                    completar_parcela_co_catastro(session, actor_actual, parcela, catastral)
                else:
                    actualizar_parcela(session, actor_actual, parcela, **(cambios or {}))

            ok = executar_accion(session, accion)
        if ok:
            ui.navigate.reload()

    def amosar(titulo: str, lineas: list[str], puntos: Any, crear: Any, completar: Any) -> None:
        """Ventá co que trae o SIGPAC ou o Catastro; o contorno queda realzado mentres está
        aberta."""
        realce = (mapa.generic_layer(name="polygon", args=[list(puntos), {"color": "#f9a825"}])
                  if puntos else None)
        with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
            ui.label(titulo).classes("text-h6")
            for linea in lineas:
                ui.label(linea)
            nome = ui.input("Nome da parcela nova").classes("w-full")
            with ui.row():
                ui.button("Crear parcela nova", icon="add",
                          on_click=lambda: crear(nome.value or ""))
                ui.button("Completar a parcela escollida", icon="edit",
                          on_click=completar).props("outline")
                ui.button("Pechar", on_click=dialogo.close).props("flat")
        dialogo.on("hide", lambda: mapa.remove_layer(realce) if realce else None)
        dialogo.open()

    def amosar_recinto(recinto: Recinto) -> None:
        amosar("Recinto SIGPAC", [f"Referencia: {recinto.referencia}",
                                  f"Uso: {recinto.uso or '—'}"], recinto.puntos,
               lambda nome: gardar(recinto=recinto, nome=nome),
               lambda: gardar(recinto=recinto))

    def amosar_catastro(datos: ParcelaCatastral) -> None:
        lineas = [f"Referencia catastral: {datos.referencia}"]
        lineas += [f"{t}: {v}" for t, v in (("Localización", datos.localizacion),
                                             ("Clase", datos.clase), ("Uso", datos.uso)) if v]
        if datos.superficie_m2:
            lineas.append(f"Superficie: {datos.superficie_m2:,.0f} m²".replace(",", " "))
        for cultivo, intensidade, m2 in datos.cultivos:
            lineas.append(f"· {cultivo}{f' (intensidade {intensidade})' if intensidade else ''}"
                          f"{f': {m2:,.0f} m²'.replace(',', ' ') if m2 else ''}")
        amosar("Parcela do Catastro", lineas, datos.puntos,
               lambda nome: gardar(catastral=datos, nome=nome),
               lambda: gardar(catastral=datos))

    async def premer(e: events.GenericEventArguments) -> None:
        if debuxando["si"]:
            return
        punto = e.args["latlng"]
        lat, lon = round(punto["lat"], 6), round(punto["lng"], 6)
        if modo.value == "nada":
            return
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
            elif modo.value == "catastro":
                datos = await run.io_bound(parcela_catastral_no_punto, lat, lon)
                if datos is None:
                    ui.notify("O Catastro non devolveu ningunha parcela aí", type="warning")
                else:
                    amosar_catastro(datos)
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar: {erro}", type="negative")

    mapa.on("map-click", premer)

    def contorno(e: events.GenericEventArguments) -> None:
        aneis = e.args.get("layer", {}).get("_latlngs") or [[]]
        puntos = [(p["lat"], p["lng"]) for p in aneis[0]]
        if destino.value == "zona":
            with get_session() as session:
                actor_actual = usuario_actual(session)
                parcela = session.get(Parcela, escoller.value) if escoller.value else None
                if actor_actual is None:
                    return
                if parcela is None:
                    ui.notify("Escolle primeiro a parcela", type="warning")
                    return
                ok = executar_accion(session, lambda: crear_zona(
                    session, actor_actual, parcela, nome_zona.value or "", tipo_zona.value,
                    puntos))
            if ok:
                ui.navigate.reload()
            return
        try:
            geojson, hectareas, centro_p = xeometria_debuxada(puntos)
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="warning")
            return
        gardar({"geometria": geojson, "lat": centro_p[0], "lon": centro_p[1],
                "superficie": hectareas})

    mapa.on("draw:created", contorno)
