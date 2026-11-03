"""Prototipo «As miñas terras» (2026-11-03): os recintos SIGPAC da explotación e, dentro de
cada un, os cultivos (a DGC do RD 1054/2022). Para probar o manexo do mapa: aínda non garda
na base de datos, só na sesión do navegador da persoa (app.storage.user)."""

from __future__ import annotations

import json
from typing import Any

from nicegui import app, events, run, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.parcela import Parcela
from horta.services.errors import OperacionNonPermitidaError
from horta.services.parcelas import xeometria_debuxada
from horta.services.xeo_oficial import (
    Recinto,
    SenConexion,
    recinto_no_punto,
    recintos_da_parcela,
    referencia_catastral_no_punto,
)
from horta.services.xeometria import dividir, recortar, xuntar
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
    const pon = (o, tipo, estilo) => {
      const l = L.polygon(o.puntos, Object.assign({bubblingMouseEvents: false}, estilo));
      l.addTo(this.grupo).bindTooltip(o.nome || "");
      l.on("click", () => emitEvent("terras_escoller", {tipo: tipo, id: o.id}));
      this.capas[tipo + ":" + o.id] = l;
    };
    const amarelo = {color: "#f9a825", weight: 5};
    datos.recintos.forEach(r => pon(r, "recinto", Object.assign(
      {color: "#2e7d32", weight: 2, fillOpacity: 0.08}, r.escollido ? amarelo : {})));
    datos.cultivos.forEach(c => pon(c, "cultivo", Object.assign(
      {color: "#ef6c00", weight: 2, fillOpacity: 0.35}, c.escollido ? amarelo : {})));
    if (datos.vista) pon({id: "vista", puntos: datos.vista, nome: "Recinto atopado"}, "vista",
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
    // Mentres se debuxa, os clics van ao debuxo e non ás terras que hai debaixo
    this.tocables(false);
    m.pm.enableDraw(forma, {snappable: true, snapDistance: 15, tooltips: false});
  },
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

# Que fai o próximo clic, e o aviso que se mostra
_AXUDA = {
    "nada": "Toca no mapa unha terra túa para atopar o seu recinto SIGPAC.",
    "debuxar": "Debuxa o cultivo: un clic en cada esquina e, para pechar, clic no primeiro "
               "punto. O que saia fóra do recinto recórtase.",
    "dividir": "Debuxa unha liña que cruce o cultivo de lado a lado; dobre clic para rematar.",
    "editar": "Arrastra os puntos dos lindes. Os puntos pequenos do medio crean un punto novo.",
    "xuntar": "Toca o outro cultivo (do mesmo recinto) que queres xuntar con este.",
}


def _ha(puntos: list[Any]) -> float:
    return xeometria_debuxada([tuple(p) for p in puntos])[1]


def _uso(codigo: str | None) -> str:
    # Só o código: a lista oficial dos usos SIGPAC aínda non está na app (pendente C5)
    return codigo or "—"


def seccion_terras(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        if usuario_actual(session) is None:
            pechar_sesion()
            return
        horta = session.get(Horta, horta_id)
        situada = session.query(Parcela).filter(
            Parcela.horta_id == horta_id, Parcela.lat.is_not(None)).first()
    clave = f"terras_proba_{horta_id}"
    datos: dict[str, Any] = app.storage.user.get(clave) or {
        "recintos": {}, "cultivos": {}, "seguinte": 1}
    sel: dict[str, Any] = {"tipo": None, "id": None, "vista": None, "modo": "nada"}

    def gardar() -> None:
        app.storage.user[clave] = json.loads(json.dumps(datos))

    with ui.column().classes("w-full gap-1 q-mb-sm"):
        ui.label("Prototipo: aínda non se garda nas parcelas da app, só para probar o mapa."
                 ).classes("etiqueta-aviso")
    ui.add_body_html(_JS)
    with ui.row().classes("w-full items-start gap-4"):
        with ui.column().classes("col-grow").style("min-width: min(100%, 22rem)"):
            axuda = ui.label(_AXUDA["nada"]).classes("text-weight-medium")
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
        panel = ui.column().classes("gap-2").style("width: min(100%, 22rem)")

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
        recintos = [{"id": r, "nome": v["finca"] or r, "puntos": v["puntos"],
                     "escollido": sel["tipo"] == "recinto" and sel["id"] == r}
                    for r, v in datos["recintos"].items()]
        cultivos = [{"id": c, "nome": v["nome"], "puntos": v["puntos"],
                     "escollido": sel["tipo"] == "cultivo" and sel["id"] == c}
                    for c, v in datos["cultivos"].items()]
        vista = sel["vista"].puntos if sel["vista"] is not None else None
        capas_js = json.dumps({"recintos": recintos, "cultivos": cultivos, "vista": vista})
        ui.run_javascript(f"terras.pintar({mapa.id}, {capas_js})")

    def refrescar() -> None:
        pintar()
        lista.refresh()

    def achegar(puntos: list[Any]) -> None:
        if puntos:
            ui.run_javascript(f"terras.achegar({mapa.id}, {json.dumps(puntos)})")

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
            ui.run_javascript(f"terras.editar('cultivo:{sel['id']}')")
        mostrar_panel.refresh()

    def escoller(tipo: str | None, ident: str | None, achegar_a: bool = False) -> None:
        if sel["modo"] != "nada":
            modo("nada")
        sel.update(tipo=tipo, id=ident)
        if tipo != "vista":
            sel["vista"] = None
        pintar()
        mostrar_panel.refresh()
        if achegar_a and tipo in ("recinto", "cultivo"):
            achegar(datos[tipo + "s"][ident]["puntos"])

    # --- O que se fai coas terras e os cultivos

    async def engadir_recinto(r: Recinto) -> None:
        if r.referencia in datos["recintos"]:
            escoller("recinto", r.referencia)
            return
        try:
            medio = xeometria_debuxada(r.puntos)[2]
            catastro = await run.io_bound(referencia_catastral_no_punto, *medio)
        except (SenConexion, ValueError):
            catastro = None
        datos["recintos"][r.referencia] = {
            "puntos": r.puntos, "uso": r.uso, "ha": _ha(r.puntos), "finca": "",
            "catastro": catastro}
        gardar()
        escoller("recinto", r.referencia)

    def novo_cultivo(recinto: str, puntos: list[Any], nome: str = "") -> None:
        cid = str(datos["seguinte"])
        datos["seguinte"] += 1
        datos["cultivos"][cid] = {"recinto": recinto, "nome": nome or f"Cultivo {cid}",
                                  "puntos": puntos, "ha": _ha(puntos)}
        gardar()
        escoller("cultivo", cid)

    def cultivos_de(recinto: str) -> list[str]:
        return [c for c, v in datos["cultivos"].items() if v["recinto"] == recinto]

    def quitar_recinto(r: str) -> None:
        for c in cultivos_de(r):
            del datos["cultivos"][c]
        del datos["recintos"][r]
        gardar()
        escoller(None, None)

    def eliminar_cultivo(c: str) -> None:
        del datos["cultivos"][c]
        gardar()
        escoller(None, None)

    async def gardar_lindes() -> None:
        c = sel["id"]
        puntos = await ui.run_javascript(f"terras.lindes('cultivo:{c}')")
        sel["modo"] = "nada"
        axuda.text = _AXUDA["nada"]
        try:
            limite = datos["recintos"][datos["cultivos"][c]["recinto"]]["puntos"]
            datos["cultivos"][c]["puntos"] = recortar([tuple(p) for p in puntos], limite)
            datos["cultivos"][c]["ha"] = _ha(datos["cultivos"][c]["puntos"])
            gardar()
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="warning")
        escoller("cultivo", c)

    # --- Eventos do mapa

    async def premer(e: events.GenericEventArguments) -> None:
        if sel["modo"] != "nada":
            return
        punto = e.args["latlng"]
        if mapa.zoom < 15:
            ui.notify("Achégate máis co zoom (+) ata ver os lindes dos recintos", type="info")
            return
        ui.notify("Buscando o recinto…", timeout=1500)
        try:
            r = await run.io_bound(recinto_no_punto, round(punto["lat"], 6),
                                   round(punto["lng"], 6))
        except (SenConexion, ValueError) as erro:
            ui.notify(f"Non se puido consultar o SIGPAC: {erro}", type="negative")
            return
        if r is None or len(r.puntos) < 3:
            ui.notify("Aí non hai ningún recinto SIGPAC", type="warning")
            return
        sel["vista"] = r
        escoller("vista", r.referencia)

    def tocar(e: events.GenericEventArguments) -> None:
        args = e.args[0] if isinstance(e.args, list) else e.args
        tipo, ident = args["tipo"], str(args["id"])
        if sel["modo"] == "xuntar" and tipo == "cultivo":
            a = sel["id"]
            if ident == a or datos["cultivos"][ident]["recinto"] != datos["cultivos"][a]["recinto"]:
                ui.notify("Escolle outro cultivo do mesmo recinto", type="warning")
                return
            try:
                unido = xuntar(datos["cultivos"][a]["puntos"], datos["cultivos"][ident]["puntos"])
            except OperacionNonPermitidaError as erro:
                ui.notify(str(erro), type="warning")
                return
            datos["cultivos"][a].update(puntos=unido, ha=_ha(unido))
            del datos["cultivos"][ident]
            gardar()
            escoller("cultivo", a)
            return
        if sel["modo"] != "nada" or tipo == "vista":
            return
        escoller(tipo, ident)

    def debuxado(e: events.GenericEventArguments) -> None:
        args = e.args[0] if isinstance(e.args, list) else e.args
        puntos = [tuple(p) for p in args["puntos"]]
        try:
            if args["forma"] == "Polygon" and sel["tipo"] == "recinto":
                r = sel["id"]
                novo_cultivo(r, recortar(puntos, datos["recintos"][r]["puntos"]))
            elif args["forma"] == "Line" and sel["tipo"] == "cultivo":
                c = sel["id"]
                orixe = datos["cultivos"][c]
                primeiro, *resto = dividir(orixe["puntos"], puntos)
                orixe.update(puntos=primeiro, ha=_ha(primeiro))
                for anaco in resto:
                    novo_cultivo(orixe["recinto"], anaco, f"{orixe['nome']} (parte)")
                gardar()
                escoller("cultivo", c)
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="warning")
            modo("nada")

    mapa.on("map-click", premer)
    ui.on("terras_escoller", tocar)
    ui.on("terras_debuxo", debuxado)

    # --- Panel da dereita: cambia segundo o que estea escollido

    @ui.refreshable
    def mostrar_panel() -> None:
        tipo, ident = sel["tipo"], sel["id"]
        if sel["modo"] != "nada":
            with ui.card().classes("w-full"):
                ui.label(_AXUDA[sel["modo"]])
                with ui.row():
                    if sel["modo"] == "editar":
                        ui.button("Gardar os lindes", icon="save", on_click=gardar_lindes)
                    ui.button("Cancelar", on_click=lambda: escoller(tipo, ident)).props("flat")
            return
        if tipo == "vista" and sel["vista"] is not None:
            r: Recinto = sel["vista"]
            with ui.card().classes("w-full"):
                ui.label("Recinto atopado").classes("text-h6")
                ui.label(f"SIGPAC {r.referencia}").classes("texto-suave")
                ui.label(f"Uso: {_uso(r.uso)} · {formatar_superficie(_ha(r.puntos))}")
                with ui.row():
                    if pode_editar:
                        ui.button("Engadir ás miñas terras", icon="add",
                                  on_click=lambda: engadir_recinto(r))
                    ui.button("Pechar", on_click=lambda: escoller(None, None)).props("flat")
        elif tipo == "recinto":
            v = datos["recintos"][ident]
            with ui.card().classes("w-full"):
                ui.label(v["finca"] or "Recinto sen nome").classes("text-h6")
                ui.label(f"SIGPAC {ident}").classes("texto-suave")
                ui.label(f"Uso: {_uso(v['uso'])} · {formatar_superficie(v['ha'])}")
                if v["catastro"]:
                    ui.label(f"Catastro {v['catastro']}").classes("texto-suave text-caption")
                if pode_editar:
                    def pon_finca(e: events.ValueChangeEventArguments, r: str = ident) -> None:
                        datos["recintos"][r]["finca"] = e.value or ""
                        gardar()
                    ui.input("Nome ou finca (o mesmo nome xunta varios recintos)",
                             value=v["finca"]).classes("w-full").on(
                        "blur", refrescar).on_value_change(pon_finca)
                    with ui.column().classes("gap-1 w-full"):
                        ui.button("Cultivo en todo o recinto", icon="crop_square",
                                  on_click=lambda: novo_cultivo(ident, v["puntos"])
                                  ).classes("w-full")
                        ui.button("Debuxar un cultivo", icon="draw",
                                  on_click=lambda: modo("debuxar")).props("outline"
                                                                          ).classes("w-full")
                        ui.button("Quitar das miñas terras", icon="remove_circle_outline",
                                  on_click=lambda: quitar_recinto(ident)).props(
                            "flat color=negative")
        elif tipo == "cultivo":
            v = datos["cultivos"][ident]
            with ui.card().classes("w-full"):
                ui.label(v["nome"]).classes("text-h6")
                ui.label(f"{formatar_superficie(v['ha'])} · no recinto {v['recinto']}"
                         ).classes("texto-suave")
                if pode_editar:
                    def pon_nome(e: events.ValueChangeEventArguments, c: str = ident) -> None:
                        datos["cultivos"][c]["nome"] = e.value or ""
                        gardar()
                    ui.input("Nome (que tes plantado)", value=v["nome"]).classes("w-full").on(
                        "blur", refrescar).on_value_change(pon_nome)
                    with ui.column().classes("gap-1 w-full"):
                        ui.button("Editar os lindes", icon="edit_location_alt",
                                  on_click=lambda: modo("editar")).classes("w-full")
                        ui.button("Dividir cunha liña", icon="content_cut",
                                  on_click=lambda: modo("dividir")).props("outline"
                                                                          ).classes("w-full")
                        ui.button("Xuntar con outro", icon="join_full",
                                  on_click=lambda: modo("xuntar")).props("outline"
                                                                         ).classes("w-full")
                        ui.button("Eliminar", icon="delete",
                                  on_click=lambda: eliminar_cultivo(ident)).props(
                            "flat color=negative")
                ui.button("Ver o seu recinto", on_click=lambda: escoller(
                    "recinto", v["recinto"])).props("flat dense")
        else:
            buscar_por_referencia()
        lista()

    def buscar_por_referencia() -> None:
        with ui.expansion("Buscar pola referencia da PAC", icon="search").classes("w-full"):
            provincia = ui.select(_PROVINCIAS, value="15", label="Provincia").classes("w-full")
            with ui.row().classes("no-wrap gap-2"):
                concello = ui.input("Concello (nº)").classes("w-24")
                poligono = ui.input("Polígono").classes("w-24")
                parcela = ui.input("Parcela").classes("w-24")

            async def buscar() -> None:
                if not (concello.value and poligono.value and parcela.value):
                    ui.notify("Enche concello, polígono e parcela", type="warning")
                    return
                try:
                    atopados = await run.io_bound(recintos_da_parcela, provincia.value,
                                                  concello.value.strip(), poligono.value.strip(),
                                                  parcela.value.strip())
                except (SenConexion, ValueError) as erro:
                    ui.notify(f"Non se puido consultar o SIGPAC: {erro}", type="negative")
                    return
                atopados = [r for r in atopados or [] if len(r.puntos) >= 3]
                if not atopados:
                    ui.notify("Non se atopou esa parcela no SIGPAC", type="warning")
                    return
                for r in atopados:
                    await engadir_recinto(r)
                achegar([p for r in atopados for p in r.puntos])
                ui.notify(f"Engadidos {len(atopados)} recintos")

            ui.button("Buscar e engadir", icon="search", on_click=buscar)

    @ui.refreshable
    def lista() -> None:
        ui.label("As miñas terras").classes("text-weight-medium q-mt-sm")
        if not datos["recintos"]:
            ui.label("Aínda ningunha. Toca as túas terras no mapa (achégate co zoom ata ver "
                     "os recintos) ou búscaas pola referencia da PAC.").classes("texto-suave")
            return
        fincas: dict[str, list[str]] = {}
        for r, v in datos["recintos"].items():
            fincas.setdefault(v["finca"] or "Sen nome", []).append(r)
        for finca, recintos in sorted(fincas.items()):
            total = sum(datos["recintos"][r]["ha"] for r in recintos)
            ui.label(f"{finca} · {formatar_superficie(total)}").classes("text-caption q-mt-xs")
            for r in recintos:
                v = datos["recintos"][r]
                with ui.item(on_click=lambda r=r: escoller("recinto", r, True)).props(
                        "clickable dense").classes("w-full rounded-borders" + (
                            " bg-amber-2" if sel["id"] == r else "")):
                    with ui.item_section():
                        ui.item_label(f"{r.split(':', 4)[-1].replace(':', '-')} · {_uso(v['uso'])}")
                        ui.item_label(formatar_superficie(v["ha"])).props("caption")
                for c in cultivos_de(r):
                    vc = datos["cultivos"][c]
                    with ui.item(on_click=lambda c=c: escoller("cultivo", c, True)).props(
                            "clickable dense").classes("w-full q-pl-lg rounded-borders" + (
                                " bg-amber-2" if sel["id"] == c else "")):
                        with ui.item_section().props("avatar"):
                            ui.icon("spa", color="orange-8")
                        with ui.item_section():
                            ui.item_label(vc["nome"])
                            ui.item_label(formatar_superficie(vc["ha"])).props("caption")

    with panel:
        mostrar_panel()

    async def iniciar() -> None:
        await mapa.initialized()
        capa("sigpac", True)
        pintar()
        todos = [p for v in datos["recintos"].values() for p in v["puntos"]]
        achegar(todos)

    ui.timer(0.1, iniciar, once=True)
