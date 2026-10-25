"""Sección Parcelas: un só formulario para crear e editar, cos campos do REA (DGC)."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.parcela import Parcela, SecanoRegadio
from horta.services.catalogos import valores_vixentes
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA

_CATALOGOS = {
    "rexime_tenencia": "rexime_tenencia",
    "causa_baixa": "causa_baixa",
    "orixe_auga": "orixe_auga",
}
_SIGPAC = (("sigpac_provincia", "Provincia"), ("sigpac_concello", "Concello"),
           ("sigpac_agregado", "Agregado"), ("sigpac_zona", "Zona"),
           ("sigpac_poligono", "Polígono"), ("sigpac_parcela", "Parcela"),
           ("sigpac_subparcela", "Recinto"))


def _referencia(p: Parcela) -> str:
    partes = [getattr(p, campo) for campo, _ in _SIGPAC]
    return ":".join(x or "-" for x in partes) if any(partes) else ""


def seccion_parcelas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        opcions = {
            campo: {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}
            for campo, catalogo in _CATALOGOS.items()
        }

    filas = [
        {"id": p.id, "nome": p.nome, "superficie": formatar_superficie(p.superficie),
         "sigpac": _referencia(p),
         "rega": {SecanoRegadio.SECANO: "Secano", SecanoRegadio.REGADIO: "Regadío"}.get(
             p.secano_regadio, "") if p.secano_regadio else "",
         "estado": p.estado}
        for p in parcelas
    ]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("nome", "Nome"), ("superficie", "Superficie"), ("sigpac", "SIGPAC"),
            ("rega", "Secano/regadío"), ("estado", "Estado"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai parcelas" {TEXTOS_TABOA}')

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Nova parcela").classes("text-h6")
        nome = ui.input("Nome").classes("w-full")
        superficie = CampoSuperficie("Superficie")
        secano = ui.select({"secano": "Secano", "regadio": "Regadío"}, label="Secano ou regadío",
                           clearable=True).classes("w-full")
        orixe_auga = ui.select(opcions["orixe_auga"], label="Orixe da auga de rega",
                               clearable=True).classes("w-full")
        uso = ui.input("Uso ou aproveitamento").classes("w-full")
        ui.label("Referencia SIGPAC").classes("text-subtitle2 q-mt-sm")
        sigpac: dict[str, Any] = {}
        with ui.grid(columns=4).classes("w-full gap-2"):
            for campo, etiqueta in _SIGPAC:
                sigpac[campo] = ui.input(etiqueta)
        catastro = ui.input("Referencia catastral").classes("w-full")
        with ui.expansion("Tenencia, alta e baixa").classes("w-full"):
            tenencia = ui.select(opcions["rexime_tenencia"], label="Réxime de tenencia",
                                 clearable=True).classes("w-full")
            nif_arrendador = ui.input("NIF do arrendador ou cedente").classes("w-full")
            pequena = ui.checkbox("Pequena superficie")
            data_alta = campo_data("Data de alta")
            data_baixa = campo_data("Data de baixa")
            causa_baixa = ui.select(opcions["causa_baixa"], label="Causa da baixa",
                                    clearable=True).classes("w-full")
        with ui.expansion("Auga para consumo humano e zonas protexidas").classes("w-full"):
            auga = ui.checkbox("Hai un pozo ou toma de auga para consumo humano na parcela "
                               "ou preto")
            with ui.column().classes("w-full gap-1").bind_visibility_from(auga, "value"):
                auga_dentro = ui.checkbox("Está dentro da parcela")
                auga_distancia = ui.input("Distancia á parcela (m)").classes("w-full")
                auga_utm = ui.input("Coordenadas UTM (opcional)").classes("w-full")
                auga_nome = ui.input("Nome do pozo ou da masa de auga").classes("w-full")
            zona = ui.select({"total": "Toda a parcela", "parcial": "Parte da parcela"},
                             label="Está nunha zona protexida (captación, hábitats, especies)",
                             clearable=True).classes("w-full")
            zona_ha = ui.input("Superficie afectada (ha), se se sabe").classes("w-full")
        with ui.expansion("Localización e notas").classes("w-full"):
            lat = ui.input("Latitude").classes("w-full")
            lon = ui.input("Lonxitude").classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            datos: dict[str, Any] = dict(
                superficie=superficie.ha,
                secano_regadio=SecanoRegadio(secano.value) if secano.value else None,
                orixe_auga=orixe_auga.value, uso_aproveitamento=uso.value or None,
                referencia_catastral=catastro.value or None,
                rexime_tenencia=tenencia.value, nif_arrendador=nif_arrendador.value or None,
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
                        crear_parcela(session, actor, horta_id, nome.value, **datos)
                    else:
                        parcela = session.get(Parcela, editando["id"])
                        if parcela is not None:
                            actualizar_parcela(session, actor, parcela, nome=nome.value, **datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    textos = (nome, uso, catastro, nif_arrendador, data_alta, data_baixa, lat, lon, notas,
              auga_distancia, auga_utm, auga_nome, zona_ha, *sigpac.values())
    selectores = (secano, orixe_auga, tenencia, causa_baixa, zona)

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Nova parcela"
        for campo in textos:
            campo.value = ""
        for selector in selectores:
            selector.value = None
        pequena.value = auga.value = auga_dentro.value = False
        superficie.establecer(None)
        dialogo.open()

    def _texto(valor: Any) -> str:
        return "" if valor is None else str(valor)

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha parcela na táboa", type="warning")
            return
        p = next(x for x in parcelas if x.id == taboa.selected[0]["id"])
        editando["id"] = p.id
        titulo.text = "Editar parcela"
        nome.value = p.nome
        superficie.establecer(p.superficie)
        secano.value = p.secano_regadio.value if p.secano_regadio else None
        orixe_auga.value = p.orixe_auga
        uso.value = _texto(p.uso_aproveitamento)
        for campo, entrada in sigpac.items():
            entrada.value = _texto(getattr(p, campo))
        catastro.value = _texto(p.referencia_catastral)
        tenencia.value = p.rexime_tenencia
        nif_arrendador.value = _texto(p.nif_arrendador)
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
        dialogo.open()

    def eliminar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha parcela na táboa", type="warning")
            return
        parcela_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                parcela = session.get(Parcela, parcela_id)
                if actor is None or parcela is None:
                    return
                ok = executar_accion(session, lambda: eliminar_parcela(session, actor, parcela))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion("Eliminar esta parcela e os seus cultivos?", confirmar)

    with ui.row():
        ui.button("Nova parcela", icon="add", on_click=abrir_nova)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")
        ui.button("Eliminar", icon="delete", on_click=eliminar).props("outline color=negative")
