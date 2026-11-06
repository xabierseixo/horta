"""Mapa das terras: as parcelas da explotación (cada unha un recinto SIGPAC) e, dentro de
cada unha, as zonas de cultivo e bancais (a DGC do RD 1054/2022 art. 2.1.d). Tocar no mapa
sempre fai algo: nunha parcela túa escóllea; fóra, busca o recinto SIGPAC dese punto."""

from __future__ import annotations

import json
from typing import Any, Callable

from nicegui import events, run, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.models.zona import ParcelaZona
from horta.services.parcelas import (
    actualizar_parcela,
    eliminar_parcela,
    listar_parcelas,
    puntos_da_xeometria,
    ten_historial,
    xeometria_debuxada,
)
from horta.services.xeo_oficial import (
    Leira,
    Recinto,
    SenConexion,
    crear_parcela_da_leira,
    marcar_parcela_na_leira,
    recinto_no_punto,
    recintos_da_parcela,
    referencia_catastral_no_punto,
)
from horta.services.zonas import (
    TIPOS_ZONA,
    borrar_zona,
    cambiar_zona,
    crear_zona,
    dividir_en_bancais,
    dividir_zona,
    xuntar_zonas,
)
from horta.ui.accions import executar_accion
from horta.ui.baixa_parcela import dialogo_baixa_parcela
from horta.ui.ficha_parcela import seccions_ficha_parcela
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import formatar_superficie

_GEOMAN = "https://unpkg.com/@geoman-io/leaflet-geoman-free@2.17.0/dist/leaflet-geoman"
_GALICIA = (42.75, -8.0)
_PROVINCIAS = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}


# O debuxo e a edición fanse no navegador (Leaflet-Geoman); o resto, en Python
_JS = """
<script>
window.terras = {
  mapa(id) { return getElement(id).map; },
  pintar(id, datos) {
    const m = this.mapa(id);
    if (this.grupo) this.grupo.remove();
    this.grupo = L.featureGroup().addTo(m);
    this.capas = {};
    const amarelo = {color: "#f9a825", weight: 5};
    const pon = (o, tipo, estilo) => {
      const e = Object.assign({bubblingMouseEvents: false}, estilo, o.escollido ? amarelo : {});
      const l = o.puntos.length ? L.polygon(o.puntos, e)
                                : L.circleMarker(o.centro, Object.assign({radius: 10}, e));
      l.addTo(this.grupo).bindTooltip(o.nome || "");
      l.on("click", () => emitEvent("terras_escoller", {tipo: tipo, id: o.id}));
      this.capas[tipo + ":" + o.id] = l;
    };
    datos.parcelas.forEach(p => pon(p, "parcela",
      {color: "#2e7d32", weight: 3, fillOpacity: 0.12}));
    datos.zonas.forEach(z => pon(z, "zona", {color: "#ef6c00", weight: 2, fillOpacity: 0.4}));
    if (datos.vista) pon({id: 0, puntos: datos.vista, nome: "Recinto atopado"}, "vista",
                         {color: "#1565c0", weight: 4, dashArray: "6", fillOpacity: 0.15});
  },
  achegar(id, puntos) { this.mapa(id).fitBounds(L.latLngBounds(puntos), {maxZoom: 19}); },
  debuxar(id, forma) {
    const m = this.mapa(id);
    m.off("pm:create");
    m.once("pm:create", (e) => {
      const ll = e.layer.getLatLngs();
      const puntos = (forma === "Line" ? ll : ll[0]).map(p => [p.lat, p.lng]);
      e.layer.remove();
      emitEvent("terras_debuxo", {forma: forma, puntos: puntos});
    });
    this.tocables(false);
    m.pm.enableDraw(forma, {snappable: true, snapDistance: 15, tooltips: false});
  },
  // Mentres se debuxa ou se marca, os clics pasan ao mapa e non ás terras de debaixo
  tocables(si) {
    Object.values(this.capas || {}).forEach(l => {
      const el = l.getElement && l.getElement();
      if (el) el.style.pointerEvents = si ? "" : "none";
    });
  },
  editar(clave) { this.capas[clave].pm.enable({snappable: true}); },
  lindes(clave) {
    const l = this.capas[clave];
    l.pm.disable();
    return l.getLatLngs()[0].map(p => [p.lat, p.lng]);
  },
  parar(id) {
    const m = this.mapa(id);
    m.pm.disableDraw();
    m.off("pm:create");
    Object.values(this.capas || {}).forEach(l => l.pm && l.pm.disable());
    this.tocables(true);
  },
};
</script>
"""

# O que fai o próximo clic, e o aviso que se mostra
_AXUDA = {
    "nada": "Toca unha parcela túa para traballar con ela, ou toca calquera terra para "
            "buscar o seu recinto SIGPAC e engadila.",
    "marcar": "Toca no mapa o recinto onde está esta parcela.",
    "debuxar": "Debuxa a zona: un clic en cada esquina e, para pechar, clic no primeiro "
               "punto. O que saia fóra da parcela recórtase.",
    "dividir": "Debuxa unha liña que cruce a zona de lado a lado; para rematar, clic outra "
               "vez no último punto.",
    "editar": "Arrastra os puntos dos lindes. Os puntos pequenos do medio crean un punto novo.",
    "xuntar": "Toca a outra zona (da mesma parcela) que queres xuntar con esta.",
}


def _uso(codigo: str | None) -> str:
    # Só o código: a lista oficial dos usos SIGPAC aínda non está na app (pendente C5)
    return codigo or "—"


def _referencia(p: Parcela) -> str | None:
    if not p.sigpac_poligono:
        return None
    return f"{p.sigpac_poligono}-{p.sigpac_parcela}-{p.sigpac_subparcela}"


def _da_referencia(p: Parcela, r: Recinto) -> bool:
    return (p.sigpac_provincia, p.sigpac_concello, p.sigpac_poligono, p.sigpac_parcela,
            p.sigpac_subparcela) == (r.provincia, r.municipio, r.poligono, r.parcela, r.recinto)


def seccion_terras(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        horta = session.get(Horta, horta_id)
        parcelas = listar_parcelas(session, actor, horta_id)
    sel: dict[str, Any] = {"tipo": None, "id": None, "vista": None, "modo": "nada"}
    datos: dict[str, Any] = {"parcelas": [], "zonas": []}

    def cargar() -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            datos["parcelas"] = listar_parcelas(session, actor, horta_id)
            ids = [p.id for p in datos["parcelas"]]
            datos["zonas"] = list(session.query(ParcelaZona).filter(
                ParcelaZona.parcela_id.in_(ids)).order_by(ParcelaZona.id)) if ids else []

    def parcela(ident: int | None) -> Parcela | None:
        return next((p for p in datos["parcelas"] if p.id == ident), None)

    def zona(ident: int | None) -> ParcelaZona | None:
        return next((z for z in datos["zonas"] if z.id == ident), None)

    def facer(accion: Callable[[Any, Any], object]) -> bool:
        """Executa unha acción na BD (cos permisos do servizo) e volve cargar os datos."""
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return False
            ok = executar_accion(session, lambda: accion(session, actor))
        cargar()
        return ok

    ui.add_body_html(_JS)
    with ui.row().classes("w-full items-start gap-4"):
        with ui.column().classes("col-grow").style("min-width: min(100%, 22rem)"):
            axuda = ui.label(_AXUDA["nada"]).classes("text-weight-medium")
            situada = next((p for p in parcelas if p.lat is not None and p.lon is not None),
                           None)
            centro: tuple[float, float] = (
                (situada.lat, situada.lon)
                if situada and situada.lat is not None and situada.lon is not None
                else (horta.lat, horta.lon) if horta and horta.lat and horta.lon
                else _GALICIA)
            mapa = ui.leaflet(center=centro, zoom=17 if centro != _GALICIA else 9,
                              additional_resources=[_GEOMAN + ".css", _GEOMAN + ".js"]
                              ).classes("w-full").style("height: 65vh")
            with ui.row().classes("items-center gap-4"):
                ui.label("Ver:").classes("texto-suave")
                caixas = {c: ui.checkbox(n, value=c == "sigpac").props("dense")
                          for c, n in (("pnoa", "Foto aérea"), ("sigpac", "Recintos SIGPAC"))}
        panel = ui.column().classes("gap-2").style("width: min(100%, 24rem)")

    capas: dict[str, Any] = {}

    def capa(nome: str, activa: bool) -> None:
        if not activa and nome in capas:
            mapa.remove_layer(capas.pop(nome))
        elif activa and nome not in capas:
            capas[nome] = mapa.tile_layer(
                url_template=f"/teselas/{nome}/{{z}}/{{x}}/{{y}}",
                options={"maxZoom": 21, "maxNativeZoom": 19, "zIndex": 1 if nome == "pnoa" else 10,
                         "minZoom": 0 if nome == "pnoa" else 15})

    for nome, caixa in caixas.items():
        caixa.on_value_change(lambda e, n=nome: capa(n, e.value))

    # --- Debuxo no mapa

    def pintar() -> None:
        def escollido(tipo: str, ident: int) -> bool:
            return sel["tipo"] == tipo and sel["id"] == ident

        en_mapa = []
        for p in datos["parcelas"]:
            puntos = puntos_da_xeometria(p.geometria)
            if puntos or p.lat is not None:
                en_mapa.append({"id": p.id, "nome": p.nome, "puntos": puntos,
                                "centro": [p.lat, p.lon], "escollido": escollido("parcela", p.id)})
        zonas = [{"id": z.id, "nome": z.nome, "puntos": puntos_da_xeometria(z.geometria),
                  "escollido": escollido("zona", z.id)}
                 for z in datos["zonas"] if puntos_da_xeometria(z.geometria)]
        vista = sel["vista"].puntos if sel["vista"] is not None else None
        capas_js = json.dumps({"parcelas": en_mapa, "zonas": zonas, "vista": vista})
        ui.run_javascript(f"terras.pintar({mapa.id}, {capas_js})")

    def refrescar() -> None:
        pintar()
        mostrar_panel.refresh()

    def achegar(puntos: list[Any]) -> None:
        if puntos:
            ui.run_javascript(f"terras.achegar({mapa.id}, {json.dumps(puntos)})")

    def achegar_a(tipo: str, ident: int) -> None:
        obxecto = parcela(ident) if tipo == "parcela" else zona(ident)
        if obxecto is None:
            return
        puntos = puntos_da_xeometria(obxecto.geometria)
        if puntos:
            achegar(puntos)
        elif isinstance(obxecto, Parcela) and obxecto.lat is not None and obxecto.lon is not None:
            mapa.set_center((obxecto.lat, obxecto.lon))
            mapa.set_zoom(18)

    def modo(novo: str) -> None:
        if sel["modo"] != "nada":
            ui.run_javascript(f"terras.parar({mapa.id})")
        sel["modo"] = novo
        axuda.text = _AXUDA[novo]
        if novo == "debuxar":
            ui.run_javascript(f"terras.debuxar({mapa.id}, 'Polygon')")
        elif novo == "dividir":
            ui.run_javascript(f"terras.debuxar({mapa.id}, 'Line')")
        elif novo == "editar":
            ui.run_javascript(f"terras.editar('zona:{sel['id']}')")
        elif novo == "marcar":
            ui.run_javascript("terras.tocables(false)")
        mostrar_panel.refresh()
        if novo != "nada":
            ui.run_javascript(f"getElement({mapa.id}).$el.scrollIntoView({{block: 'center'}})")

    def escoller(tipo: str | None, ident: int | None, achegar_ao: bool = False) -> None:
        if sel["modo"] != "nada":
            modo("nada")
        sel.update(tipo=tipo, id=ident, modo="nada")
        axuda.text = _AXUDA["nada"]
        if tipo != "vista":
            sel["vista"] = None
        refrescar()
        if achegar_ao and tipo in ("parcela", "zona") and ident is not None:
            achegar_a(tipo, ident)
            ui.run_javascript(f"getElement({mapa.id}).$el.scrollIntoView({{block: 'start'}})")

    # --- O que se fai coas terras e as zonas

    async def catastro_de(r: Recinto) -> str | None:
        try:
            return await run.io_bound(referencia_catastral_no_punto,
                                      *xeometria_debuxada(r.puntos)[2])
        except (SenConexion, ValueError):
            return None

    async def engadir(r: Recinto, nome: str = "") -> int | None:
        """Crea a parcela do recinto (ou devolve a que xa o ten)."""
        xa = next((p for p in datos["parcelas"] if _da_referencia(p, r)), None)
        if xa is not None:
            return xa.id
        catastro = await catastro_de(r)
        creada: dict[str, int] = {}

        def accion(session: Any, actor: Any) -> None:
            p = crear_parcela_da_leira(session, actor, horta_id, nome, Leira(None, r))
            if catastro:
                actualizar_parcela(session, actor, p, referencia_catastral=catastro)
            creada["id"] = p.id

        facer(accion)
        return creada.get("id")

    async def engadir_vista(nome: str) -> None:
        r = sel["vista"]
        ident = await engadir(r, nome)
        if ident is not None:
            ui.notify("Gardada nas túas parcelas", type="positive")
            escoller("parcela", ident)

    async def marcar_en(ident: int, r: Recinto) -> None:
        if any(_da_referencia(p, r) for p in datos["parcelas"] if p.id != ident):
            ui.notify("Ese recinto xa é doutra parcela túa", type="warning")
            return
        catastro = await catastro_de(r)

        def accion(session: Any, actor: Any) -> None:
            p = session.get(Parcela, ident)
            marcar_parcela_na_leira(session, actor, p, Leira(None, r))
            if catastro:
                actualizar_parcela(session, actor, p, referencia_catastral=catastro)

        if facer(accion):
            ui.notify("Parcela marcada no mapa", type="positive")
        escoller("parcela", ident, True)

    def nova_zona(ident: int, puntos: list[Any], nome: str, tipo: str = "cultivo") -> None:
        creada: dict[str, int] = {}

        def accion(session: Any, actor: Any) -> None:
            p = session.get(Parcela, ident)
            creada["id"] = crear_zona(session, actor, p, nome, tipo, puntos, so_dentro=True).id

        facer(accion)
        if creada:
            escoller("zona", creada["id"])
        else:
            escoller("parcela", ident)

    def con_zona(ident: int, accion: Callable[[Any, Any, ParcelaZona], object]) -> bool:
        return facer(lambda session, actor: accion(session, actor,
                                                   session.get(ParcelaZona, ident)))

    async def gardar_lindes() -> None:
        ident = sel["id"]
        puntos = await ui.run_javascript(f"terras.lindes('zona:{ident}')")
        sel["modo"] = "nada"
        con_zona(ident, lambda s, a, z: cambiar_zona(s, a, z, puntos=[tuple(p) for p in puntos]))
        escoller("zona", ident)

    async def quitar_parcela(ident: int) -> None:
        p = parcela(ident)
        with get_session() as session:
            con_historial = p is not None and ten_historial(session, p)
        if con_historial:
            def tras_baixa() -> None:
                cargar()
                escoller(None, None)

            dialogo_baixa_parcela(ident, tras_baixa)
            return
        with ui.dialog() as confirmar, ui.card():
            ui.label(f"Quitar «{p.nome if p else ''}» e as súas zonas?")
            with ui.row():
                ui.button("Quitar", color="negative", on_click=lambda: confirmar.submit(True))
                ui.button("Non", on_click=lambda: confirmar.submit(False)).props("flat")
        if await confirmar and facer(lambda s, a: eliminar_parcela(s, a, s.get(Parcela, ident))):
            escoller(None, None)

    def quitar_zona(ident: int) -> None:
        z = zona(ident)
        if con_zona(ident, lambda s, a, zz: borrar_zona(s, a, zz)):
            escoller("parcela", z.parcela_id if z else None)

    # --- Eventos do mapa

    async def premer(e: events.GenericEventArguments) -> None:
        if sel["modo"] not in ("nada", "marcar"):
            return
        punto = e.args["latlng"]
        ui.notify("Buscando o recinto SIGPAC…", timeout=1500)
        try:
            r = await run.io_bound(recinto_no_punto, round(punto["lat"], 6),
                                   round(punto["lng"], 6))
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar o SIGPAC: {erro}", type="negative")
            return
        if r is None or len(r.puntos) < 3:
            ui.notify("Aí non hai ningún recinto SIGPAC", type="warning")
            return
        if sel["modo"] == "marcar":
            await marcar_en(sel["id"], r)
            return
        xa = next((p for p in datos["parcelas"] if _da_referencia(p, r)), None)
        if xa is not None:
            escoller("parcela", xa.id)
            return
        sel["vista"] = r
        escoller("vista", 0)
        achegar(r.puntos)

    def tocar(e: events.GenericEventArguments) -> None:
        args = e.args[0] if isinstance(e.args, list) else e.args
        tipo, ident = args["tipo"], int(args["id"])
        if sel["modo"] == "xuntar" and tipo == "zona":
            a = sel["id"]
            if con_zona(a, lambda s, act, z: xuntar_zonas(s, act, z, s.get(ParcelaZona, ident))):
                ui.notify("Zonas xuntadas", type="positive")
            escoller("zona", a)
            return
        if sel["modo"] != "nada" or tipo == "vista":
            return
        escoller(tipo, ident)

    def debuxado(e: events.GenericEventArguments) -> None:
        args = e.args[0] if isinstance(e.args, list) else e.args
        puntos = [tuple(p) for p in args["puntos"]]
        ident = sel["id"]
        if args["forma"] == "Polygon" and sel["tipo"] == "parcela":
            n = sum(1 for z in datos["zonas"] if z.parcela_id == ident) + 1
            nova_zona(ident, puntos, f"Zona {n}")
        elif args["forma"] == "Line" and sel["tipo"] == "zona":
            if con_zona(ident, lambda s, a, z: dividir_zona(s, a, z, puntos)):
                ui.notify("Zona dividida", type="positive")
            escoller("zona", ident)

    mapa.on("map-click", premer)
    ui.on("terras_escoller", tocar)
    ui.on("terras_debuxo", debuxado)

    # --- Panel: cambia segundo o que estea escollido

    with (ui.dialog() as dialogo_bancais, ui.card().style("width: min(26rem, 94vw)")):
        ui.label("Dividir a parcela en bancais iguais").classes("text-h6")
        cantos = ui.number("Cantos bancais", value=4, min=1, step=1).classes("w-full")
        direccion = ui.select({0: "Norte–sur", 90: "Leste–oeste"}, value=0,
                              label="Dirección dos bancais").classes("w-full")
        paso = ui.number("Paso entre bancais (m)", value=0.5, min=0, step=0.1).classes("w-full")

        def facer_bancais() -> None:
            ident = sel["id"]
            if facer(lambda s, a: dividir_en_bancais(
                    s, a, s.get(Parcela, ident), int(cantos.value or 0),
                    float(direccion.value or 0), float(paso.value or 0))):
                dialogo_bancais.close()
                escoller("parcela", ident)

        with ui.row():
            ui.button("Dividir", icon="view_week", on_click=facer_bancais)
            ui.button("Cancelar", on_click=dialogo_bancais.close).props("flat")

    def renomear_parcela(ident: int, valor: str) -> None:
        p = parcela(ident)
        if p is not None and valor.strip() and valor.strip() != p.nome:
            facer(lambda s, a: actualizar_parcela(s, a, s.get(Parcela, ident), nome=valor.strip()))
            refrescar()

    def renomear_zona(ident: int, valor: str) -> None:
        z = zona(ident)
        if z is not None and valor.strip() and valor.strip() != z.nome:
            con_zona(ident, lambda s, a, zz: cambiar_zona(s, a, zz, nome=valor))
            refrescar()

    def boton(texto: str, icona: str, accion: Callable[[], Any], principal: bool = False
              ) -> None:
        b = ui.button(texto, icon=icona, on_click=accion).classes("w-full")
        if not principal:
            b.props("outline")

    @ui.refreshable
    def mostrar_panel() -> None:
        tipo, ident = sel["tipo"], sel["id"]
        if sel["modo"] != "nada":
            with ui.card().classes("w-full bg-amber-1"):
                ui.label(_AXUDA[sel["modo"]]).classes("text-weight-medium")
                with ui.row():
                    if sel["modo"] == "editar":
                        ui.button("Gardar os lindes", icon="save", on_click=gardar_lindes)
                    ui.button("Cancelar", on_click=lambda: escoller(tipo, ident)).props("flat")
            return
        p = parcela(ident) if tipo == "parcela" else None
        z = zona(ident) if tipo == "zona" else None
        if tipo == "vista" and sel["vista"] is not None:
            r: Recinto = sel["vista"]
            with ui.card().classes("w-full"):
                ui.label("Recinto atopado").classes("text-h6")
                ui.label(f"SIGPAC {r.poligono}-{r.parcela}-{r.recinto} · Uso {_uso(r.uso)}")
                ui.label(formatar_superficie(xeometria_debuxada(r.puntos)[1])
                         ).classes("texto-suave")
                if pode_editar:
                    nome = ui.input("Nome para a parcela",
                                    value=f"Leira {r.poligono}-{r.parcela}-{r.recinto}"
                                    ).classes("w-full")
                    boton("Engadir ás miñas parcelas", "add",
                          lambda: engadir_vista(nome.value or ""), principal=True)
                    sen_mapa = [x for x in datos["parcelas"]
                                if not puntos_da_xeometria(x.geometria)]
                    if sen_mapa:
                        ui.label("Ou é unha parcela que xa tes sen marcar:"
                                 ).classes("texto-suave q-mt-sm")
                        for x in sen_mapa:
                            def esta(ident: int = x.id) -> Any:
                                return marcar_en(ident, r)
                            boton(f"É «{x.nome}»", "push_pin", esta)
                ui.button("Pechar", on_click=lambda: escoller(None, None)).props("flat")
        elif p is not None:
            with ui.card().classes("w-full"):
                if pode_editar:
                    ui.input("Nome da parcela", value=p.nome).classes("w-full text-h6").on(
                        "blur", lambda e, i=p.id: renomear_parcela(i, e.sender.value or ""))
                else:
                    ui.label(p.nome).classes("text-h6")
                ref = _referencia(p)
                ui.label(f"SIGPAC {ref} · Uso {_uso(p.uso_aproveitamento)}" if ref
                         else "Sen recinto SIGPAC").classes("texto-suave")
                if p.referencia_catastral:
                    ui.label(f"Catastro {p.referencia_catastral}").classes("texto-suave")
                ui.label(formatar_superficie(p.superficie) if p.superficie else ""
                         ).classes("texto-suave")
                seccions_ficha_parcela(horta_id, p.id, pode_editar)
                contorno = puntos_da_xeometria(p.geometria)
                if pode_editar:
                    with ui.column().classes("gap-1 w-full q-mt-sm"):
                        if contorno:
                            boton("Debuxar unha zona de cultivo", "draw",
                                  lambda: modo("debuxar"), principal=True)
                            boton("Toda a parcela é unha zona de cultivo", "crop_square",
                                  lambda: nova_zona(p.id, contorno, p.nome))
                            boton("Dividir en bancais", "view_week", dialogo_bancais.open)
                            boton("Cambiar o recinto", "push_pin", lambda: modo("marcar"))
                        else:
                            boton("Marcar no mapa", "push_pin", lambda: modo("marcar"),
                                  principal=True)
                        ui.button("Quitar esta parcela", icon="delete",
                                  on_click=lambda: quitar_parcela(p.id)).props(
                            "flat color=negative")
        elif z is not None:
            dona = parcela(z.parcela_id)
            with ui.card().classes("w-full"):
                if pode_editar:
                    ui.input("Nome da zona (que tes plantado)", value=z.nome).classes(
                        "w-full text-h6").on(
                        "blur", lambda e, i=z.id: renomear_zona(i, e.sender.value or ""))
                else:
                    ui.label(z.nome).classes("text-h6")
                ui.label(f"{TIPOS_ZONA.get(z.tipo, z.tipo)} · "
                         f"{formatar_superficie(z.superficie or 0)}").classes("texto-suave")
                if pode_editar:
                    with ui.column().classes("gap-1 w-full q-mt-sm"):
                        boton("Mover os lindes", "edit_location_alt", lambda: modo("editar"),
                              principal=True)
                        boton("Dividir cunha liña", "content_cut", lambda: modo("dividir"))
                        boton("Xuntar con outra zona", "join_full", lambda: modo("xuntar"))
                        ui.button("Quitar esta zona", icon="delete",
                                  on_click=lambda: quitar_zona(z.id)).props(
                            "flat color=negative")
                if dona is not None:
                    ui.button(f"Volver a «{dona.nome}»", icon="arrow_back",
                              on_click=lambda: escoller("parcela", dona.id)).props("flat dense")
        else:
            if pode_editar:
                buscar_por_referencia()
        lista()

    def buscar_por_referencia() -> None:
        with ui.expansion("Buscar pola referencia da PAC", icon="search").classes("w-full"):
            provincia = ui.select(_PROVINCIAS, value="15", label="Provincia").classes("w-full")
            with ui.row().classes("no-wrap gap-2"):
                concello = ui.input("Concello (nº)").classes("w-24")
                poligono = ui.input("Polígono").classes("w-24")
                num = ui.input("Parcela").classes("w-24")

            async def buscar() -> None:
                if not (concello.value and poligono.value and num.value):
                    ui.notify("Enche concello, polígono e parcela", type="warning")
                    return
                try:
                    atopados = await run.io_bound(recintos_da_parcela, provincia.value,
                                                  concello.value.strip(), poligono.value.strip(),
                                                  num.value.strip())
                except (SenConexion, ValueError) as erro:
                    ui.notify(f"Non se puido consultar o SIGPAC: {erro}", type="negative")
                    return
                atopados = [r for r in atopados or [] if len(r.puntos) >= 3]
                if not atopados:
                    ui.notify("Non se atopou esa parcela no SIGPAC", type="warning")
                    return
                for r in atopados:
                    await engadir(r)
                ui.notify(f"Gardados {len(atopados)} recintos nas túas parcelas",
                          type="positive")
                escoller(None, None)
                achegar([pt for r in atopados for pt in r.puntos])

            ui.button("Buscar e engadir", icon="search", on_click=buscar)

    def lista() -> None:
        ui.label("As miñas parcelas").classes("text-weight-medium q-mt-sm")
        if not datos["parcelas"]:
            ui.label("Aínda ningunha. Toca as túas terras no mapa ou búscaas pola "
                     "referencia da PAC.").classes("texto-suave")
            return
        for p in datos["parcelas"]:
            ref = _referencia(p)
            with ui.item(on_click=lambda p=p: escoller("parcela", p.id, True)).props(
                    "clickable dense").classes("w-full rounded-borders" + (
                        " bg-amber-2" if sel["tipo"] == "parcela" and sel["id"] == p.id
                        else "")):
                with ui.item_section().props("avatar"):
                    ui.icon("crop_free" if puntos_da_xeometria(p.geometria) else "help_outline",
                            color="green-8" if p.geometria else "grey")
                with ui.item_section():
                    ui.item_label(p.nome)
                    ui.item_label(" · ".join(x for x in (
                        ref or ("debuxada a man" if p.geometria else "sen marcar no mapa"),
                        formatar_superficie(p.superficie) if p.superficie else "") if x)
                    ).props("caption")
            for z in (z for z in datos["zonas"] if z.parcela_id == p.id):
                with ui.item(on_click=lambda z=z: escoller("zona", z.id, True)).props(
                        "clickable dense").classes("w-full q-pl-lg rounded-borders" + (
                            " bg-amber-2" if sel["tipo"] == "zona" and sel["id"] == z.id
                            else "")):
                    with ui.item_section().props("avatar"):
                        ui.icon("spa", color="orange-8")
                    with ui.item_section():
                        ui.item_label(z.nome)
                        ui.item_label(formatar_superficie(z.superficie or 0)).props("caption")

    cargar()
    with panel:
        mostrar_panel()

    async def iniciar() -> None:
        await mapa.initialized()
        capa("sigpac", True)
        pintar()
        todos = [pt for p in datos["parcelas"] for pt in puntos_da_xeometria(p.geometria)]
        achegar(todos)

    ui.timer(0.1, iniciar, once=True)

