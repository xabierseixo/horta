"""Calendario e mapa da explotación (paso 13): os traballos e tarefas por día, e as parcelas
no mapa: as leiras (Catastro + SIGPAC) fanse parcelas premendo nelas."""

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
    Leira,
    SenConexion,
    crear_parcela_da_leira,
    leira_no_punto,
    marcar_parcela_na_leira,
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
    "nada": "Preme nunha das túas parcelas (no mapa ou na lista) para escollela.",
    "leiras": "Preme nas leiras que queres engadir: cada clic marca unha (en azul); "
              "premer outra vez nela desmárcaa. Achégate co zoom para ver os lindes.",
    "marcar": "Preme na leira onde está esta parcela.",
    "debuxar_nova": "Debuxa a parcela co botón do pentágono (arriba á esquerda do mapa): "
                    "un clic en cada esquina e, para pechar, clic no primeiro punto.",
    "debuxar_contorno": "Debuxa o contorno co botón do pentágono (arriba á esquerda do mapa).",
    "debuxar_zona": "Debuxa a zona de cultivo co botón do pentágono (arriba á esquerda do "
                    "mapa), dentro da parcela.",
}
_AMARELO, _AZUL, _VERDE = "#f9a825", "#1565c0", "#2e7d32"


def _referencias(p: Parcela) -> str:
    partes = []
    if p.sigpac_poligono is not None:
        partes.append(f"SIGPAC {p.sigpac_provincia}:{p.sigpac_concello}:{p.sigpac_agregado or 0}:"
                      f"{p.sigpac_zona or 0}:{p.sigpac_poligono}:{p.sigpac_parcela}:"
                      f"{p.sigpac_subparcela}")
    if p.referencia_catastral:
        partes.append(f"Catastro {p.referencia_catastral}")
    return " · ".join(partes)


def _hectareas(leira: Leira) -> float | None:
    if len(leira.puntos) >= 3:
        return xeometria_debuxada(leira.puntos)[1]
    m2 = leira.catastral.superficie_m2 if leira.catastral else None
    return m2 / 10000 if m2 else None


def _clave(leira: Leira) -> str:
    return leira.catastral.referencia if leira.catastral else (
        leira.recinto.referencia if leira.recinto else "")


def _limites(puntos: list[tuple[float, float]]) -> list[list[float]]:
    lats, lons = [p[0] for p in puntos], [p[1] for p in puntos]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]


def seccion_mapa(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        horta = session.get(Horta, horta_id)
        parcelas = list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(
            Parcela.nome))
        zonas = {p.id: listar_zonas(session, actor, p) for p in parcelas}
        avisos = [a for p in parcelas if (a := aviso_superficie(session, p))]
    por_id = {p.id: p for p in parcelas}
    clave_escollida = f"mapa_parcela_{horta_id}"
    estado: dict[str, Any] = {"modo": "nada", "escollida": None, "realce": None}
    if app.storage.user.get(clave_escollida) in por_id:
        estado["escollida"] = por_id[app.storage.user[clave_escollida]]
    # As leiras marcadas para engadir: clave → (leira, capa no mapa)
    marcadas: dict[str, tuple[Leira, Any]] = {}
    situadas = [(p, (p.lat, p.lon)) for p in parcelas if p.lat is not None and p.lon is not None]
    centro = ((estado["escollida"].lat, estado["escollida"].lon)
              if estado["escollida"] is not None and estado["escollida"].lat is not None
              else situadas[0][1] if situadas
              else (horta.lat, horta.lon) if horta and horta.lat and horta.lon else _GALICIA)
    debuxo = ({"draw": {"polygon": True, "marker": False, "circlemarker": False,
                        "polyline": False, "rectangle": False, "circle": False},
               # Sen o lapis nin a papeleira do debuxo: non tocan as parcelas e confunden
               "edit": {"edit": False, "remove": False}} if pode_editar else False)

    with ui.row().classes("w-full items-start gap-4"):
        with ui.column().classes("col-grow").style("min-width: min(100%, 22rem)"):
            mapa = ui.leaflet(center=centro, zoom=17 if situadas else 8, draw_control=debuxo,
                              hide_drawn_items=True).classes("w-full mapa-parcelas").style(
                "height: 62vh")
            capas_fila = ui.row().classes("items-center gap-4")
        lista = ui.column().classes("gap-1").style("width: min(100%, 20rem)")
    ui.add_css(".mapa-parcelas .leaflet-draw-toolbar:has(.leaflet-draw-edit-edit) "
               "{display: none}")
    for p, punto in situadas:
        if not puntos_da_xeometria(p.geometria):
            mapa.marker(latlng=punto).run_method("bindTooltip", p.nome)
    for p in parcelas:
        forma = puntos_da_xeometria(p.geometria)
        if forma:
            mapa.generic_layer(name="polygon", args=[forma, {"color": _VERDE}]
                               ).run_method("bindTooltip", p.nome)
        for z in zonas[p.id]:
            forma_z = puntos_da_xeometria(z.geometria)
            if forma_z:
                mapa.generic_layer(name="polygon", args=[forma_z, {
                    "color": "#ef6c00", "weight": 1, "dashArray": "4"}]).run_method(
                    "bindTooltip", f"{p.nome} · {z.nome}")

    # Capas oficiais (as imaxes pídeas o navegador). Todas pasan pola caché da app
    # (/teselas): sen conexión vese o xa descargado. A ortofoto vai debaixo; SIGPAC e
    # Catastro por riba (e só con zoom, que é cando os debuxan)
    capas: dict[str, Any] = {}
    caixas: dict[str, Any] = {}

    def capa(clave: str, activa: bool) -> None:
        if not activa and clave in capas:
            mapa.remove_layer(capas.pop(clave))
        elif activa and clave not in capas:
            _nome, atribucion, zindex, zoom_min = CAPAS[clave]
            capas[clave] = mapa.tile_layer(url_template=f"/teselas/{clave}/{{z}}/{{x}}/{{y}}",
                                           options={"attribution": atribucion, "maxZoom": 21,
                                                    "maxNativeZoom": 19, "minZoom": zoom_min,
                                                    "zIndex": zindex})

    with capas_fila:
        ui.label("Ver:").classes("texto-suave")
        for clave, (nome, *_) in CAPAS.items():
            caixas[clave] = ui.checkbox(nome, on_change=lambda e, c=clave: capa(c, e.value)
                                        ).props("dense")
        ui.button(icon="download_for_offline", on_click=lambda: gardar_sen_conexion()).props(
            "flat dense round").tooltip("Gardar o mapa arredor das parcelas para velo sen "
                                        "cobertura")

    async def gardar_sen_conexion() -> None:
        puntos = [pt for p in parcelas for pt in (puntos_da_xeometria(p.geometria) or (
            [(p.lat, p.lon)] if p.lat is not None and p.lon is not None else []))]
        if not puntos:
            ui.notify("Marca antes algunha parcela no mapa", type="warning")
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

    # --- Lista das parcelas (á dereita, ou debaixo no móbil)
    with lista:
        if pode_editar:
            ui.button("Engadir leiras", icon="add_location_alt",
                      on_click=lambda: cambiar("leiras")).classes("w-full")
        ui.label("As túas parcelas").classes("text-weight-medium q-mt-sm")
        if not parcelas:
            ui.label("Aínda non tes ningunha. Preme «Engadir leiras» e despois toca as túas "
                     "leiras no mapa.").classes("texto-suave")
        filas: dict[int, Any] = {}
        for p in parcelas:
            with ui.item(on_click=lambda p=p: escoller_parcela(p, achegar=True)).props(
                    "clickable dense").classes("w-full rounded-borders") as fila:
                with ui.item_section():
                    ui.item_label(p.nome)
                    ui.item_label(formatar_superficie(p.superficie) if p.superficie else "—"
                                  ).props("caption")
                if not puntos_da_xeometria(p.geometria):
                    with ui.item_section().props("side"):
                        ui.badge("sen marcar" if p.lat is None else "só un punto",
                                 color="orange").props("outline")
            filas[p.id] = fila
        for aviso in avisos:
            ui.label(aviso).classes("etiqueta-aviso")

    # --- Barra do que fai o próximo clic, as leiras marcadas e a ficha da escollida
    with ui.row().classes("items-center gap-2 q-mt-sm"):
        aviso_modo = ui.label(_MODOS["nada"]).classes("text-weight-medium")
        cancelar = ui.button("Cancelar", on_click=lambda: cambiar("nada")).props("flat dense")
    with ui.row().classes("items-center gap-2") as barra_leiras:
        resumo_leiras = ui.label()
        gardar_leiras_btn = ui.button("Gardalas como parcelas", icon="save",
                                      on_click=lambda: dialogo_leiras())
        ui.button("A leira non aparece? Debúxaa", icon="pentagon",
                  on_click=lambda: cambiar("debuxar_nova")).props("flat dense")
    with ui.row().classes("items-center gap-2") as campos_zona:
        tipo_zona = ui.select(TIPOS_ZONA, value="bancal", label="Tipo de zona").classes("w-48")
        nome_zona = ui.input("Nome da zona").classes("w-48")
    ficha = ui.column().classes("w-full")

    def cambiar(modo: str) -> None:
        if estado["modo"] == "leiras" and modo != "leiras":
            for _leira, capa_l in marcadas.values():
                mapa.remove_layer(capa_l)
            marcadas.clear()
        estado["modo"] = modo
        aviso_modo.text = _MODOS[modo]
        cancelar.set_visibility(modo != "nada")
        campos_zona.set_visibility(modo == "debuxar_zona")
        barra_leiras.set_visibility(modo == "leiras")
        if modo in ("leiras", "marcar") and not caixas["catastro"].value:
            caixas["catastro"].value = True  # para ver os lindes das leiras
        if modo != "nada":  # que se vexa o mapa, onde vai o próximo clic
            ui.run_javascript(f"document.getElementById('c{mapa.id}')"
                              ".scrollIntoView({behavior: 'smooth', block: 'center'})")
        actualizar_leiras()

    def actualizar_leiras() -> None:
        total = sum(h for leira, _ in marcadas.values() if (h := _hectareas(leira)))
        resumo_leiras.text = (f"{len(marcadas)} leiras marcadas · {formatar_superficie(total)}"
                              if marcadas else "Ningunha leira marcada aínda")
        gardar_leiras_btn.set_enabled(bool(marcadas))

    def escoller_parcela(p: Parcela | None, achegar: bool = False) -> None:
        estado["escollida"] = p
        app.storage.user[clave_escollida] = p.id if p else None
        for pid, fila in filas.items():
            fila.classes(add="bg-amber-2" if p and pid == p.id else "",
                         remove="" if p and pid == p.id else "bg-amber-2")
        if estado["realce"] is not None:
            mapa.remove_layer(estado["realce"])
            estado["realce"] = None
        forma = puntos_da_xeometria(p.geometria) if p else []
        if forma:
            estado["realce"] = mapa.generic_layer(name="polygon", args=[forma, {
                "color": _AMARELO, "weight": 5, "fillOpacity": 0.35}])
            if achegar:
                mapa.run_map_method("fitBounds", _limites(forma), {"maxZoom": 19})
        elif p is not None and p.lat is not None and p.lon is not None:
            estado["realce"] = mapa.generic_layer(name="circleMarker", args=[
                (p.lat, p.lon), {"radius": 16, "color": _AMARELO, "weight": 5}])
            if achegar:
                mapa.set_center((p.lat, p.lon))
        if estado["modo"] in ("marcar", "debuxar_contorno", "debuxar_zona"):
            cambiar("nada")
        debuxar_ficha()

    def debuxar_ficha() -> None:
        ficha.clear()
        p = estado["escollida"]
        if p is None:
            return
        con_contorno = bool(puntos_da_xeometria(p.geometria))
        with ficha, ui.card().classes("w-full"):
            ui.label(p.nome).classes("text-h6")
            ui.label(formatar_superficie(p.superficie) if p.superficie else "Sen superficie")
            if _referencias(p):
                ui.label(_referencias(p)).classes("texto-suave text-caption")
            if not pode_editar:
                return
            if not con_contorno:
                ui.label("Esta parcela aínda non ten os lindes no mapa.").classes(
                    "etiqueta-aviso")
            with ui.row().classes("gap-2"):
                ui.button("Marcar no mapa" if not con_contorno else "Cambiar a leira",
                          icon="add_location_alt", on_click=lambda: cambiar("marcar")).props(
                    "" if not con_contorno else "outline")
                if con_contorno:
                    ui.button("Debuxar zona de cultivo", icon="grid_view",
                              on_click=lambda: cambiar("debuxar_zona"))
                    ui.button("Dividir en bancais", icon="view_week",
                              on_click=lambda: dividir_dialogo.open()).props("outline")
                ui.button("Eliminar", icon="delete", on_click=eliminar).props(
                    "flat color=negative")

    cancelar.set_visibility(False)
    campos_zona.set_visibility(False)
    barra_leiras.set_visibility(False)

    # As zonas de cada parcela, para borralas
    with ui.expansion("Zonas de cultivo", icon="grid_view").classes("w-full q-mt-sm"):
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

    def dialogo_leiras() -> None:
        """Un nome para cada leira marcada, e gárdanse todas como parcelas."""
        nomes: list[tuple[Leira, Any]] = []
        with (ui.dialog().props("persistent") as dialogo,
              ui.card().style("width: min(32rem, 94vw)")):
            ui.label("Gardar as leiras como parcelas").classes("text-h6")
            ui.label("Ponlle a cada unha o nome co que a coñeces.").classes("texto-suave")
            for leira, _capa in marcadas.values():
                h = _hectareas(leira)
                nomes.append((leira, ui.input(
                    f"Nome ({formatar_superficie(h)})" if h else "Nome",
                    value=leira.nome).classes("w-full")))

            def crear_todas() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        return
                    creadas: list[Parcela] = []

                    def accion() -> None:
                        for leira, nome in nomes:
                            creadas.append(crear_parcela_da_leira(
                                session, actor_actual, horta_id, nome.value or "", leira))

                    ok = executar_accion(session, accion)
                if ok:
                    app.storage.user[clave_escollida] = creadas[-1].id if creadas else None
                    ui.navigate.reload()

            with ui.row():
                ui.button("Gardar", icon="save", on_click=crear_todas)
                ui.button("Volver", on_click=dialogo.close).props("flat")
        dialogo.open()

    async def buscar_leira(lat: float, lon: float) -> Leira | None:
        ui.notify("Buscando a leira…", timeout=1500)
        try:
            leira = await run.io_bound(leira_no_punto, lat, lon)
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar: {erro}", type="negative")
            return None
        if leira is None:
            ui.notify("Aí non se atopa ningunha leira. Se é túa, debúxaa.", type="warning")
        return leira

    async def marcar_leira(lat: float, lon: float) -> None:
        dentro = parcela_no_punto([p for p in parcelas if puntos_da_xeometria(p.geometria)],
                                  lat, lon)
        if dentro is not None:
            ui.notify(f"Aí xa está a túa parcela «{dentro.nome}»", type="info")
            return
        leira = await buscar_leira(lat, lon)
        if leira is None or estado["modo"] != "leiras":
            return
        clave = _clave(leira)
        if clave in marcadas:  # segundo clic: desmárcase
            mapa.remove_layer(marcadas.pop(clave)[1])
        elif leira.puntos:
            marcadas[clave] = (leira, mapa.generic_layer(name="polygon", args=[
                leira.puntos, {"color": _AZUL, "weight": 4, "fillOpacity": 0.3}]))
        else:
            ui.notify("Esta leira non trae os lindes; gárdase só coa superficie", type="info")
            marcadas[clave] = (leira, mapa.generic_layer(name="circleMarker", args=[
                (lat, lon), {"radius": 12, "color": _AZUL}]))
        actualizar_leiras()

    async def leira_da_escollida(lat: float, lon: float) -> None:
        leira = await buscar_leira(lat, lon)
        p = estado["escollida"]
        if leira is None or p is None:
            return
        realce = (mapa.generic_layer(name="polygon", args=[leira.puntos, {
            "color": _AZUL, "weight": 4}]) if leira.puntos else None)
        h = _hectareas(leira)
        with (ui.dialog().props("persistent") as dialogo,
              ui.card().style("width: min(30rem, 94vw)")):
            ui.label("É esta a leira?").classes("text-h6")
            ui.label(f"«{p.nome}» quedará co contorno marcado en azul"
                     + (f" ({formatar_superficie(h)})." if h else "."))
            with ui.row():
                ui.button("Si, é esta", icon="check", on_click=lambda: gardar(da_escollida(
                    lambda s, a, parcela: marcar_parcela_na_leira(s, a, parcela, leira))))
                def debuxala() -> None:
                    dialogo.close()
                    cambiar("debuxar_contorno")

                ui.button("Non: debuxala eu", on_click=debuxala).props("flat")
                ui.button("Pechar", on_click=dialogo.close).props("flat")
        dialogo.on("hide", lambda: mapa.remove_layer(realce) if realce else None)
        dialogo.open()

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
        if modo == "leiras":
            await marcar_leira(lat, lon)
        elif modo == "marcar":
            await leira_da_escollida(lat, lon)
        elif (escollida := parcela_no_punto(parcelas, lat, lon)) is not None:
            escoller_parcela(escollida)
        elif modo == "nada":
            ui.notify("Aí non hai ningunha parcela túa. Para engadila, preme «Engadir leiras»")

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
