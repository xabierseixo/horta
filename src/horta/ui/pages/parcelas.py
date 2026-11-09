"""Sección Parcelas: un só formulario para crear e editar, cos campos do REA (DGC)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.parcela import Parcela, SecanoRegadio
from horta.services.catalogos import valores_vixentes
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
    ten_historial,
)
from horta.services.tempo import gardar_lugar
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion
from horta.ui.baixa_parcela import dialogo_baixa_parcela
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.etiquetas import ESTADOS_PARCELA
from horta.ui.fotos import abrir_fotos
from horta.ui.historial import abrir_historial
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import CampoLugarTempo

_CATALOGOS = {
    "rexime_tenencia": "rexime_tenencia",
    "causa_baixa": "causa_baixa",
    "orixe_auga": "orixe_auga",
}
_SIGPAC = (("sigpac_provincia", N_("Provincia")), ("sigpac_concello", N_("Concello")),
           ("sigpac_agregado", N_("Agregado")), ("sigpac_zona", N_("Zona")),
           ("sigpac_poligono", N_("Polígono")), ("sigpac_parcela", N_("Parcela")),
           ("sigpac_subparcela", N_("Recinto")))


def _referencia(p: Parcela) -> str:
    """Polígono-parcela-recinto, como se le no SIGPAC (X7); o resto vai no formulario."""
    if not p.sigpac_poligono:
        return ""
    return f"{p.sigpac_poligono}-{p.sigpac_parcela or '-'}-{p.sigpac_subparcela or '-'}"


def seccion_parcelas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        opcions = {
            campo: {
                v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                for v in valores_vixentes(session, catalogo)
            }
            for campo, catalogo in _CATALOGOS.items()
        }

    filas = [
        {"id": p.id, "nome": p.nome, "superficie": formatar_superficie(p.superficie),
         "sigpac": _referencia(p),
         "rega": {SecanoRegadio.SECANO: _("Secano"), SecanoRegadio.REGADIO: _("Regadío")}.get(
             p.secano_regadio, "") if p.secano_regadio else "",
         "estado": _(ESTADOS_PARCELA[p.estado]) if p.estado in ESTADOS_PARCELA else p.estado}
        for p in parcelas
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", _("Nome")), ("superficie", _("Superficie")), ("sigpac", "SIGPAC"),
            ("rega", _("Secano/regadío")), ("estado", _("Estado")))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="{_("Aínda non hai parcelas")}" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "nome", ["superficie", "rega"], accions_tarxeta)

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label(_("Nova parcela")).classes("text-h6")
        nome = ui.input(_("Nome")).classes("w-full")
        superficie = CampoSuperficie(_("Superficie"))
        secano = ui.select({"secano": _("Secano"), "regadio": _("Regadío")},
                           label=_("Secano ou regadío"),
                           clearable=True).classes("w-full")
        orixe_auga = ui.select(opcions["orixe_auga"], label=_("Orixe da auga de rega"),
                               clearable=True).classes("w-full")
        uso = ui.input(_("Uso ou aproveitamento")).classes("w-full")
        ui.label(_("Referencia SIGPAC")).classes("text-subtitle2 q-mt-sm")
        sigpac: dict[str, Any] = {}
        with ui.grid(columns=4).classes("w-full gap-2"):
            for campo, etiqueta in _SIGPAC:
                sigpac[campo] = ui.input(_(etiqueta))
        catastro = ui.input(_("Referencia catastral")).classes("w-full")
        with ui.expansion(_("Tenencia, alta e baixa")).classes("w-full"):
            tenencia = ui.select(opcions["rexime_tenencia"], label=_("Réxime de tenencia"),
                                 clearable=True).classes("w-full")
            arrendador = CampoPersoa(horta_id, None, _("Quen a arrenda ou cede"))
            pequena = ui.checkbox(_("Pequena superficie"))
            data_alta = campo_data(_("Data de alta"))
            data_baixa = campo_data(_("Data de baixa"))
            causa_baixa = ui.select(opcions["causa_baixa"], label=_("Causa da baixa"),
                                    clearable=True).classes("w-full")
        with ui.expansion(_("Auga para consumo humano e zonas protexidas")).classes("w-full"):
            auga = ui.checkbox(_("Hai un pozo ou toma de auga para consumo humano na parcela "
                                 "ou preto"))
            with ui.column().classes("w-full gap-1").bind_visibility_from(auga, "value"):
                auga_dentro = ui.checkbox(_("Está dentro da parcela"))
                auga_distancia = ui.input(_("Distancia á parcela (m)")).classes("w-full")
                auga_utm = ui.input(_("Coordenadas UTM (opcional)")).classes("w-full")
                auga_nome = ui.input(_("Nome do pozo ou da masa de auga")).classes("w-full")
            zona = ui.select({"total": _("Toda a parcela"), "parcial": _("Parte da parcela")},
                             label=_("Está nunha zona protexida (captación, hábitats, especies)"),
                             clearable=True).classes("w-full")
            zona_ha = ui.input(_("Superficie afectada (ha), se se sabe")).classes("w-full")
        with ui.expansion(_("Localización e notas")).classes("w-full"):
            lat = ui.input(_("Latitude")).classes("w-full")
            lon = ui.input(_("Lonxitude")).classes("w-full")
            notas = ui.textarea(_("Notas")).classes("w-full")
        with ui.expansion(_("O tempo")).classes("w-full"):
            lugar = CampoLugarTempo(_("O da explotación"))

        def situar() -> None:
            try:
                lugar.situar(parsear_decimal(lat.value), parsear_decimal(lon.value))
            except ValueError:
                lugar.situar(None, None)

        for coordenada in (lat, lon):
            coordenada.on_value_change(situar)

        def gardar() -> None:
            if not nome.value:
                ui.notify(_("O nome é obrigatorio"), type="negative")
                return
            datos: dict[str, Any] = dict(
                superficie=superficie.ha,
                secano_regadio=SecanoRegadio(secano.value) if secano.value else None,
                orixe_auga=orixe_auga.value, uso_aproveitamento=uso.value or None,
                referencia_catastral=catastro.value or None,
                rexime_tenencia=tenencia.value, arrendador_id=arrendador.value,
                pequena_superficie=pequena.value,
                data_alta=parsear_data(data_alta.value), data_baixa=parsear_data(data_baixa.value),
                causa_baixa=causa_baixa.value,
                lat=parsear_decimal(lat.value), lon=parsear_decimal(lon.value),
                notas=notas.value or None,
                auga_consumo=auga.value, auga_consumo_na_parcela=auga_dentro.value,
                auga_consumo_distancia_m=parsear_decimal(auga_distancia.value),
                auga_consumo_utm=auga_utm.value or None,
                auga_consumo_denominacion=auga_nome.value or None,
                zona_especifica=zona.value, zona_especifica_ha=parsear_decimal(zona_ha.value),
                **{campo: (entrada.value or None) for campo, entrada in sigpac.items()},
            )
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    if editando["id"] is None:
                        parcela = crear_parcela(session, actor, horta_id, nome.value, **datos)
                    else:
                        existente = session.get(Parcela, editando["id"])
                        if existente is None:
                            return
                        parcela = actualizar_parcela(session, actor, existente, nome=nome.value,
                                                     **datos)
                    gardar_lugar(session, actor, parcela, lugar.concello_ine,
                                 lugar.estacion_escollida)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    textos = (nome, uso, catastro, data_alta, data_baixa, lat, lon, notas,
              auga_distancia, auga_utm, auga_nome, zona_ha, *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa, zona)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = _("Nova parcela")
        for campo in textos:
            campo.value = ""
        for selector in selectores:
            selector.value = None
        arrendador.value = None
        pequena.value = auga.value = auga_dentro.value = False
        superficie.establecer(None)
        lugar.cargar(None, None, None, None)
        dialogo.open()

    def _texto(valor: Any) -> str:
        return "" if valor is None else str(valor)

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona unha parcela na táboa"), type="warning")
            return
        p = next(x for x in parcelas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = _("Editar parcela")
        nome.value = p.nome
        superficie.establecer(p.superficie)
        secano.value = p.secano_regadio.value if p.secano_regadio else None
        orixe_auga.value = p.orixe_auga
        uso.value = _texto(p.uso_aproveitamento)
        for campo, entrada in sigpac.items():
            entrada.value = _texto(getattr(p, campo))
        catastro.value = _texto(p.referencia_catastral)
        tenencia.value = p.rexime_tenencia
        arrendador.value = p.arrendador_id
        pequena.value = p.pequena_superficie
        data_alta.value = _texto(p.data_alta)
        data_baixa.value = _texto(p.data_baixa)
        causa_baixa.value = p.causa_baixa
        lat.value = _texto(p.lat)
        lon.value = _texto(p.lon)
        notas.value = _texto(p.notas)
        auga.value, auga_dentro.value = p.auga_consumo, p.auga_consumo_na_parcela
        auga_distancia.value = _texto(p.auga_consumo_distancia_m)
        auga_utm.value = _texto(p.auga_consumo_utm)
        auga_nome.value = _texto(p.auga_consumo_denominacion)
        zona.value = p.zona_especifica
        zona_ha.value = _texto(p.zona_especifica_ha)
        lugar.cargar(p.concello_ine, p.estacion_meteo_id, p.lat, p.lon)
        dialogo.open()

    def historial() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona unha parcela na táboa"), type="warning")
            return
        abrir_historial("parcela", taboa.selected[0]["id"])

    def fotos() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona unha parcela na táboa"), type="warning")
            return
        abrir_fotos(horta_id, "parcela", taboa.selected[0]["id"], "parcela", pode_editar)

    def eliminar() -> None:
        if not taboa.selected:
            ui.notify(_("Selecciona unha parcela na táboa"), type="warning")
            return
        parcela_id = taboa.selected[0]["id"]
        with get_session() as session:
            escollida = session.get(Parcela, parcela_id)
            con_historial = escollida is not None and ten_historial(session, escollida)
        if con_historial:
            dialogo_baixa_parcela(parcela_id, ui.navigate.reload)
            return

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                parcela = session.get(Parcela, parcela_id)
                if actor is None or parcela is None:
                    return
                ok = executar_accion(session, lambda: eliminar_parcela(session, actor, parcela))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(_("Eliminar esta parcela e os seus cultivos?"), confirmar)

    accions_tarxeta += [(_("Editar"), "edit", abrir_edicion),
                        (_("Historial"), "history", historial),
                        (_("Fotos"), "photo_camera", fotos),
                        (_("Eliminar"), "delete", eliminar)]

    with ui.row():
        ui.button(_("Nova parcela"), icon="add", on_click=abrir_nova)
        with ui.row().classes("so-ordenador"):
            ui.button(_("Editar"), icon="edit", on_click=abrir_edicion).props("outline")
            ui.button(_("Historial"), icon="history", on_click=historial).props("outline")
            ui.button(_("Fotos"), icon="photo_camera", on_click=fotos).props("outline")
            ui.button(_("Eliminar"), icon="delete", on_click=eliminar).props(
                "outline color=negative")
