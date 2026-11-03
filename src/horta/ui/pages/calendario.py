"""Calendario e mapa da explotación (paso 13): os traballos e tarefas por día, e as parcelas
no mapa. Só len o que xa hai; no mapa pódese situar unha parcela premendo nel."""

from __future__ import annotations

from datetime import date, timedelta
from functools import partial
from typing import Any, Callable

from nicegui import app, events, run, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.models.zona import ParcelaZona
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    parcela_no_punto,
    puntos_da_xeometria,
    xeometria_debuxada,
)
from horta.services.persoas import listar_persoas
from horta.services.teselas import gardar_zona
from horta.services.xeo_oficial import (
    SenConexion,
    completar_parcela_co_catastro,
    completar_parcela_co_recinto,
    crear_parcela_do_recinto,
    parcela_catastral_no_punto,
    recinto_no_punto,
    referencia_catastral_no_punto,
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
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.pages.diario import Formularios, tarxeta
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import formatar_superficie

# capa → (nome, atribución, orde, zoom mínimo)
CAPAS = {
    "pnoa": ("Ortofoto (PNOA)", "PNOA © IGN", 1, 0),
    "sigpac": ("Recintos SIGPAC", "SIGPAC © FEGA", 10, 15),
    "catastro": ("Catastro (propiedade)", "© Dirección Xeral do Catastro", 11, 15),
}
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


# O que fai o próximo clic (ou o próximo debuxo) no mapa, e o aviso que se mostra
_MODOS = {
    "nada": "Preme nunha parcela do mapa para escollela.",
    "sigpac_nova": "Preme no recinto SIGPAC que queres traer como parcela nova.",
    "debuxar_nova": "Debuxa a parcela nova co botón do pentágono (arriba á esquerda do mapa): "
                    "un clic en cada esquina e, para pechar, clic no primeiro punto.",
    "sigpac_completar": "Preme no recinto SIGPAC desta parcela.",
    "catastro_ref": "Preme na finca do Catastro onde está esta parcela.",
    "debuxar_contorno": "Debuxa o contorno co botón do pentágono (arriba á esquerda do mapa).",
    "debuxar_zona": "Debuxa a zona co botón do pentágono (arriba á esquerda do mapa).",
    "situar": "Preme no mapa onde está a parcela.",
}


def _referencia_sigpac(p: Parcela) -> str:
    if p.sigpac_poligono is None:
        return "sen recinto SIGPAC"
    return (f"SIGPAC {p.sigpac_provincia}:{p.sigpac_concello}:{p.sigpac_agregado or 0}:"
            f"{p.sigpac_zona or 0}:{p.sigpac_poligono}:{p.sigpac_parcela}:"
            f"{p.sigpac_subparcela}")


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
    por_id = {p.id: p for p in parcelas}
    clave_escollida = f"mapa_parcela_{horta_id}"
    estado: dict[str, Any] = {"modo": "nada", "escollida": None, "realce": None}
    if app.storage.user.get(clave_escollida) in por_id:
        estado["escollida"] = por_id[app.storage.user[clave_escollida]]
    situadas = [(p, (p.lat, p.lon)) for p in parcelas if p.lat is not None and p.lon is not None]
    centro = ((estado["escollida"].lat, estado["escollida"].lon)
              if estado["escollida"] is not None and estado["escollida"].lat is not None
              else situadas[0][1] if situadas
              else (horta.lat, horta.lon) if horta and horta.lat and horta.lon else _GALICIA)
    debuxo = ({"draw": {"polygon": True, "marker": False, "circlemarker": False,
                        "polyline": False, "rectangle": False, "circle": False},
               # Sen o lapis nin a papeleira do debuxo: non tocan as parcelas e confunden
               "edit": {"edit": False, "remove": False}} if pode_editar else False)
    mapa = ui.leaflet(center=centro, zoom=16 if situadas else 8, draw_control=debuxo,
                      hide_drawn_items=True).classes("w-full mapa-parcelas").style(
        "height: 60vh")
    ui.add_css(".mapa-parcelas .leaflet-draw-toolbar:has(.leaflet-draw-edit-edit) "
               "{display: none}")
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

    # Todas pasan pola caché da app (/teselas): sen conexión vese o xa descargado. A ortofoto
    # vai debaixo; SIGPAC e Catastro por riba (e só con zoom, que é cando os debuxan)
    def capa(clave: str, activa: bool) -> None:
        if not activa and clave in capas:
            mapa.remove_layer(capas.pop(clave))
        elif activa and clave not in capas:
            nome, atribucion, zindex, zoom_min = CAPAS[clave]
            capas[clave] = mapa.tile_layer(url_template=f"/teselas/{clave}/{{z}}/{{x}}/{{y}}",
                                           options={"attribution": atribucion, "maxZoom": 21,
                                                    "maxNativeZoom": 19, "minZoom": zoom_min,
                                                    "zIndex": zindex})

    with ui.row().classes("items-center gap-4 q-mt-sm"):
        ui.label("Capas:").classes("text-weight-medium")
        for clave, (nome, *_) in CAPAS.items():
            ui.checkbox(nome, on_change=lambda e, c=clave: capa(c, e.value))
    ui.label("A ortofoto é a foto aérea. Os recintos SIGPAC (os das axudas e do caderno) e as "
             "fincas do Catastro (a propiedade) vense ao achegarse (zoom 15 ou máis)."
             ).classes("texto-suave text-caption")

    async def gardar_sen_conexion() -> None:
        puntos = [pt for p in parcelas for pt in (puntos_da_xeometria(p.geometria) or (
            [(p.lat, p.lon)] if p.lat is not None and p.lon is not None else []))]
        if not puntos:
            ui.notify("Sitúa antes algunha parcela no mapa", type="warning")
            return
        ui.notify("Descargando a zona… pode levar uns minutos")
        try:
            resultado = await run.io_bound(gardar_zona, puntos, tuple(CAPAS))
        except ValueError as erro:
            ui.notify(str(erro), type="warning")
            return
        if resultado is None:  # o cliente marchou da páxina
            return
        gardadas, fallidas = resultado
        ui.notify(f"Gardadas {gardadas} teselas para usar sen conexión"
                  + (f" ({fallidas} non se puideron descargar)" if fallidas else ""),
                  type="positive" if not fallidas else "warning")

    sen_situar = [p for p in parcelas if p.lat is None or p.lon is None]
    if sen_situar:
        ui.label("Sen situar no mapa (escóllea abaixo e prema «Situar»): "
                 + ", ".join(p.nome for p in sen_situar)).classes("texto-suave")
    for aviso in avisos:
        ui.label(aviso).classes("etiqueta-aviso")

    # --- Barra: parcela nova, o que fai o próximo clic e a ficha da parcela escollida
    with ui.row().classes("items-center gap-2 q-mt-sm"):
        if pode_editar:
            with ui.button("Nova parcela", icon="add"):
                with ui.menu():
                    ui.menu_item("Do SIGPAC (o habitual)", on_click=lambda: cambiar("sigpac_nova"))
                    ui.menu_item("Debuxándoa no mapa (se non está no SIGPAC)",
                                 on_click=lambda: cambiar("debuxar_nova"))
        escoller = ui.select({p.id: p.nome for p in parcelas}, label="Parcela escollida",
                             value=estado["escollida"].id if estado["escollida"] else None,
                             on_change=lambda e: escoller_parcela(por_id.get(e.value))
                             ).classes("w-64")
        ui.button("Gardar a zona para usar sen conexión", icon="download_for_offline",
                  on_click=gardar_sen_conexion).props("outline dense").tooltip(
            "Descarga as capas arredor das parcelas para ver o mapa sen cobertura")
    with ui.row().classes("items-center gap-2"):
        aviso_modo = ui.label(_MODOS["nada"]).classes("text-weight-medium")
        cancelar = ui.button("Cancelar", on_click=lambda: cambiar("nada")).props("flat dense")
    with ui.row().classes("items-center gap-2") as campos_zona:
        tipo_zona = ui.select(TIPOS_ZONA, value="bancal", label="Tipo de zona").classes("w-48")
        nome_zona = ui.input("Nome da zona").classes("w-48")
    ficha = ui.column().classes("w-full")

    def cambiar(modo: str) -> None:
        estado["modo"] = modo
        aviso_modo.text = _MODOS[modo]
        cancelar.set_visibility(modo != "nada")
        campos_zona.set_visibility(modo == "debuxar_zona")

    def escoller_parcela(p: Parcela | None) -> None:
        estado["escollida"] = p
        app.storage.user[clave_escollida] = p.id if p else None
        if escoller.value != (p.id if p else None):
            escoller.value = p.id if p else None
        if estado["realce"] is not None:
            mapa.remove_layer(estado["realce"])
            estado["realce"] = None
        forma = puntos_da_xeometria(p.geometria) if p else []
        if forma:
            estado["realce"] = mapa.generic_layer(name="polygon", args=[forma, {
                "color": "#f9a825", "weight": 4}])
        if estado["modo"] not in ("nada", "sigpac_nova", "debuxar_nova"):
            cambiar("nada")
        debuxar_ficha()

    def debuxar_ficha() -> None:
        ficha.clear()
        p = estado["escollida"]
        if p is None:
            return
        with ficha, ui.card().classes("w-full"):
            ui.label(p.nome).classes("text-h6")
            ui.label(f"{formatar_superficie(p.superficie)} · {_referencia_sigpac(p)} · "
                     f"Catastro: {p.referencia_catastral or '—'}").classes("texto-suave")
            if not pode_editar:
                return
            with ui.row().classes("gap-2"):
                ui.button("Traer o recinto SIGPAC", icon="travel_explore",
                          on_click=lambda: cambiar("sigpac_completar")).props("outline").tooltip(
                    "Contorno, superficie, uso e referencia oficiais")
                ui.button("Engadir a referencia catastral", icon="home_work",
                          on_click=lambda: cambiar("catastro_ref")).props("outline").tooltip(
                    "Só a referencia da finca; non cambia o contorno do SIGPAC")
                ui.button("Debuxar o contorno", icon="pentagon",
                          on_click=lambda: cambiar("debuxar_contorno")).props("outline")
                ui.button("Debuxar unha zona", icon="grid_view",
                          on_click=lambda: cambiar("debuxar_zona")).props("outline").tooltip(
                    "Un bancal, invernadoiro… dentro da parcela")
                ui.button("Dividir en bancais", icon="view_week",
                          on_click=lambda: dividir_dialogo.open()).props("outline")
                ui.button("Situar", icon="place", on_click=lambda: cambiar("situar")).props(
                    "outline").tooltip("Marcar onde está, sen contorno")
                ui.button("Eliminar", icon="delete", on_click=eliminar).props(
                    "outline color=negative")

    cancelar.set_visibility(False)
    campos_zona.set_visibility(False)

    # As zonas de cada parcela, para borralas
    with ui.expansion("Zonas das parcelas", icon="grid_view").classes("w-full q-mt-sm"):
        for p in parcelas:
            for z in zonas[p.id]:
                with ui.row().classes("items-center gap-2"):
                    ui.label(f"{p.nome} · {z.nome} ({TIPOS_ZONA[z.tipo]}): "
                             f"{(z.superficie or 0) * 10000:.0f} m²")
                    if pode_editar:
                        ui.button(icon="delete", on_click=lambda z=z: borrar(z.id)).props(
                            "flat dense round size=sm color=negative")
        if not any(zonas.values()):
            ui.label("Aínda non hai zonas.").classes("texto-suave")

    with (ui.dialog().props("persistent") as dividir_dialogo,
          ui.card().style("width: min(28rem, 94vw)")):
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
                p = estado["escollida"]
                parcela = session.get(Parcela, p.id) if p else None
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

    def borrar(zona_id: int) -> None:
        with get_session() as session:
            actor_actual = usuario_actual(session)
            zona = session.get(ParcelaZona, zona_id)
            if actor_actual is None or zona is None:
                return
            ok = executar_accion(session, lambda: borrar_zona(session, actor_actual, zona))
        if ok:
            ui.navigate.reload()

    def eliminar() -> None:
        p = estado["escollida"]
        if p is None:
            return

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                parcela = session.get(Parcela, p.id)
                if actor_actual is None or parcela is None:
                    return
                ok = executar_accion(session, lambda: eliminar_parcela(
                    session, actor_actual, parcela))
            if ok:
                app.storage.user[clave_escollida] = None
                ui.navigate.reload()

        confirmar_eliminacion(f"Eliminar a parcela «{p.nome}» e os seus cultivos?", confirmar)

    def gardar(accion_con: Callable[[Session, Usuario, Parcela | None], Parcela | None]) -> None:
        """Executa a acción coa parcela escollida (se hai) e deixa escollida a que resulte."""
        resultado: dict[str, Parcela | None] = {}
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                return
            p = estado["escollida"]
            parcela = session.get(Parcela, p.id) if p else None

            def accion() -> None:
                resultado["p"] = accion_con(session, actor_actual, parcela)

            ok = executar_accion(session, accion)
        if ok:
            if (nova := resultado.get("p")) is not None:
                app.storage.user[clave_escollida] = nova.id
            ui.navigate.reload()

    def da_escollida(fai: Callable[[Session, Usuario, Parcela], Parcela | None]
                     ) -> Callable[[Session, Usuario, Parcela | None], Parcela | None]:
        def accion(session: Session, actor_actual: Usuario, parcela: Parcela | None
                   ) -> Parcela | None:
            if parcela is None:
                raise OperacionNonPermitidaError("Escolle primeiro a parcela")
            return fai(session, actor_actual, parcela)
        return accion

    def venta(titulo: str, lineas: list[str], puntos: Any, nova: bool,
              gardar_con: Callable[[str, bool], None], texto_ref: str | None = None) -> None:
        """Ventá co que trae o SIGPAC ou o Catastro; o contorno queda realzado mentres está
        aberta."""
        realce = (mapa.generic_layer(name="polygon", args=[list(puntos), {"color": "#f9a825"}])
                  if puntos else None)
        with (ui.dialog().props("persistent") as dialogo,
              ui.card().style("width: min(32rem, 94vw)")):
            ui.label(titulo).classes("text-h6")
            for linea in lineas:
                ui.label(linea)
            con_ref = (ui.checkbox(f"Gardar tamén a referencia catastral {texto_ref}", value=True)
                       if texto_ref else None)
            nome = ui.input("Nome da parcela nova").classes("w-full") if nova else None
            p = estado["escollida"]
            with ui.row():
                ui.button("Crear a parcela" if nova else f"Gardar en «{p.nome if p else ''}»",
                          icon="add" if nova else "save", on_click=lambda: gardar_con(
                              nome.value if nome else "", bool(con_ref and con_ref.value)))
                ui.button("Pechar", on_click=dialogo.close).props("flat")
        dialogo.on("hide", lambda: mapa.remove_layer(realce) if realce else None)
        dialogo.open()

    async def traer_recinto(lat: float, lon: float, nova: bool) -> None:
        recinto = await run.io_bound(recinto_no_punto, lat, lon)
        if recinto is None:
            ui.notify("Non hai ningún recinto SIGPAC aí", type="warning")
            return
        # A finca do Catastro no medio do recinto: proponse, e a persoa decide
        try:
            medio = xeometria_debuxada(recinto.puntos)[2] if len(recinto.puntos) >= 3 else (
                lat, lon)
            ref = await run.io_bound(referencia_catastral_no_punto, medio[0], medio[1])
        except (SenConexion, ValueError, OperacionNonPermitidaError):
            ref = None

        def gardar_con(nome: str, con_ref: bool) -> None:
            r = ref if con_ref else None
            if nova:
                gardar(lambda s, a, _p: crear_parcela_do_recinto(s, a, horta_id, nome, recinto, r))
            else:
                gardar(da_escollida(lambda s, a, p: completar_parcela_co_recinto(
                    s, a, p, recinto, r)))

        venta("Recinto SIGPAC", [f"Referencia: {recinto.referencia}",
                                 f"Uso: {recinto.uso or '—'}"], recinto.puntos, nova,
              gardar_con, ref)

    async def traer_catastro(lat: float, lon: float) -> None:
        """O Catastro só complementa unha parcela que xa existe."""
        datos = await run.io_bound(parcela_catastral_no_punto, lat, lon)
        if datos is None:
            ui.notify("O Catastro non devolveu ningunha finca aí", type="warning")
            return
        lineas = [f"Referencia catastral: {datos.referencia}"]
        lineas += [f"{t}: {v}" for t, v in (("Localización", datos.localizacion),
                                             ("Clase", datos.clase), ("Uso", datos.uso)) if v]
        if datos.superficie_m2:
            lineas.append(f"Superficie: {datos.superficie_m2:,.0f} m²".replace(",", " "))
        for cultivo, intensidade, m2 in datos.cultivos:
            lineas.append(f"· {cultivo}{f' (intensidade {intensidade})' if intensidade else ''}"
                          f"{f': {m2:,.0f} m²'.replace(',', ' ') if m2 else ''}")
        p = estado["escollida"]
        if p is not None and p.sigpac_poligono is not None:
            lineas.append("Só se garda a referencia: o contorno e a superficie seguen sendo os "
                          "do SIGPAC.")

        def gardar_con(_nome: str, _con_ref: bool) -> None:
            gardar(da_escollida(lambda s, a, p: completar_parcela_co_catastro(s, a, p, datos)))

        venta("Finca do Catastro", lineas, datos.puntos, False, gardar_con)

    # Mentres se debuxa un contorno, os clics son os seus puntos
    debuxando = {"si": False}
    mapa.on("draw:drawstart", lambda: debuxando.update(si=True))
    mapa.on("draw:drawstop", lambda: debuxando.update(si=False))

    async def premer(e: events.GenericEventArguments) -> None:
        if debuxando["si"]:
            return
        punto = e.args["latlng"]
        lat, lon = round(punto["lat"], 6), round(punto["lng"], 6)
        modo = estado["modo"]
        if modo in ("nada", "debuxar_nova", "debuxar_contorno", "debuxar_zona"):
            escollida = parcela_no_punto(parcelas, lat, lon)
            if escollida is not None:
                escoller_parcela(escollida)
            elif modo == "nada":
                ui.notify("Aí non hai ningunha parcela. Para crear unha, preme «Nova parcela»")
            return
        if modo == "situar":
            gardar(da_escollida(lambda s, a, p: actualizar_parcela(s, a, p, lat=lat, lon=lon)))
            return
        ui.notify("Consultando…", timeout=1500)
        try:
            if modo in ("sigpac_nova", "sigpac_completar"):
                await traer_recinto(lat, lon, modo == "sigpac_nova")
            else:
                await traer_catastro(lat, lon)
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar: {erro}", type="negative")

    mapa.on("map-click", premer)

    def contorno(e: events.GenericEventArguments) -> None:
        aneis = e.args.get("layer", {}).get("_latlngs") or [[]]
        puntos = [(p["lat"], p["lng"]) for p in aneis[0]]
        modo = estado["modo"]
        if modo == "debuxar_zona":
            gardar(da_escollida(lambda s, a, p: (crear_zona(
                s, a, p, nome_zona.value or "", tipo_zona.value, puntos), p)[1]))
            return
        try:
            geojson, hectareas, centro_p = xeometria_debuxada(puntos)
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="warning")
            return
        cambios = {"geometria": geojson, "lat": centro_p[0], "lon": centro_p[1],
                   "superficie": hectareas}
        if modo == "debuxar_contorno":
            gardar(da_escollida(lambda s, a, p: actualizar_parcela(s, a, p, **cambios)))
            return
        # Calquera outro debuxo é unha parcela nova: pídese o nome
        with ui.dialog().props("persistent") as dialogo, ui.card():
            ui.label(f"Parcela nova de {formatar_superficie(hectareas)}").classes("text-h6")
            nome = ui.input("Nome da parcela").classes("w-full")
            with ui.row():
                ui.button("Crear a parcela", icon="add", on_click=lambda: gardar(
                    lambda s, a, _p: actualizar_parcela(s, a, crear_parcela(
                        s, a, horta_id, nome.value or "Parcela nova"), **cambios)))
                ui.button("Cancelar", on_click=dialogo.close).props("flat")
        dialogo.open()

    mapa.on("draw:created", contorno)
    # A escollida antes de gardar segue escollida despois (xa existen os botóns da ficha)
    if estado["escollida"] is not None:
        escoller_parcela(estado["escollida"])
