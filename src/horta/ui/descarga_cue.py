"""Caderno dixital (CUE): descargar os datos co formato oficial (JSON) e o Excel para pasalos
ao caderno público da Xunta (XEAGA), e ver o que lles falta por traballo
."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from functools import partial
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.envio_cue import EnvioCue
from horta.services.conexion_xeaga import (
    desconectar,
    nova_peticion,
    token_vixente,
    xeaga_configurada,
)
from horta.services.cue import excel_xeaga, json_cue, xerar_cue
from horta.services.envio_cue import comprobar, enviar, envios
from horta.services.persoas import titular_da_horta
from horta.services.rea import aceptar, comparar, ler_dgcs
from horta.services.xeaga import Token, Xeaga, XeagaErro
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.formato_descarga import descargar_informe, selector_formato
from horta.ui.layout import url_seccion
from horta.ui.numeros import parsear_data
from horta.ui.pages.diario import SECCION_DO_TIPO
from horta.ui.sesion import pechar_sesion, usuario_actual

# Onde se completa o que falta, para o que non é un traballo
_SECCION = {**SECCION_DO_TIPO, "cultivo": "cultivos", "explotacion": "explotacion"}
_RESULTADOS = {"pendente": "pendente de procesar na Xunta", "OK": "aceptado",
               "PARCIAL": "aceptado en parte", "FALLO": "rexeitado"}


def seccion_cue(horta_id: int) -> None:
    hoxe = date.today()
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-mt-md"):
        ui.label("Caderno dixital (CUE)").classes("text-subtitle1 text-weight-bold")
        ui.label("Os tratamentos fitosanitarios apúntanse nel desde o 1/1/2027. O caderno "
                 "público da Xunta (XEAGA) non importa ficheiros: o Excel ten todo ordenado "
                 "para pasalo a man. Os datos en JSON son os que enviaría un CUE comercial."
                 ).classes("texto-suave")
        with ui.row().classes("w-full no-wrap"):
            desde = campo_data("Desde", date(hoxe.year, 1, 1).isoformat()).classes(
                remove="w-full", add="col")
            ata = campo_data("Ata", hoxe.isoformat()).classes(remove="w-full", add="col")
        formato = selector_formato()

        def xerar(tipo: str) -> None:
            inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
            if inicio is None or fin is None:
                ui.notify("Indica as dúas datas", type="warning")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                cue = xerar_cue(session, actor, horta_id, inicio, fin)
            nome = f"cue-{inicio:%Y%m%d}-{fin:%Y%m%d}"
            if tipo == "json":
                ui.download.content(json_cue(cue), f"{nome}.json")
            else:
                descargar_informe(
                    excel_xeaga(cue),
                    formato.value or "xlsx",
                    f"{nome}-para-xeaga",
                    "Caderno dixital (CUE) para o XEAGA",
                    "xeaga",
                )

        with ui.row():
            ui.button("Para pasar ao XEAGA", icon="download",
                      on_click=lambda: xerar("excel")).props("outline")
            ui.button("Datos do CUE (JSON)", icon="data_object",
                      on_click=lambda: xerar("json")).props("outline flat")
        _xunta(horta_id, desde, ata)
        _faltas(horta_id, date(hoxe.year, 1, 1), hoxe)


def _xunta(horta_id: int, desde: ui.input, ata: ui.input) -> None:
    """Conectar coa Xunta, enviar o pendente e ver como quedou cada envío."""
    ui.label("Enviar ao caderno da Xunta").classes("text-subtitle2 q-mt-sm")
    ui.label("Os envíos teñen que estar feitos antes do 31 de marzo e do 30 de setembro. "
             "Unha leira lévase nun só caderno: se a levas aquí, non a leves tamén no "
             "XEAGA.").classes("texto-suave text-caption")
    xeaga = xeaga_configurada()
    if xeaga is None:
        ui.label("Para enviar desde horta, a app ten que estar dada de alta na Xunta como "
                 "caderno comercial (trámite MR407B) e o titular autorizala (MR407D). "
                 "Mentres tanto, descarga o Excel e pásao ao XEAGA.").classes("texto-suave")
        return

    @ui.refreshable
    def bloque() -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            token = token_vixente(actor.id, horta_id)
            lista = envios(session, actor, horta_id)[:10]
        if token is None:
            def conectar() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        return
                    peticion = nova_peticion(actor_actual.id, horta_id)
                ui.navigate.to(xeaga.url_acceso(peticion))

            ui.button("Conectar coa Xunta", icon="login", on_click=conectar)
            ui.label("Identifícaste na Xunta co teu certificado ou Chave365 e volves aquí. "
                     "horta non ve as túas claves.").classes("texto-suave text-caption")
        else:
            def mandar() -> None:
                inicio, fin = parsear_data(desde.value), parsear_data(ata.value)
                if inicio is None or fin is None:
                    ui.notify("Indica as dúas datas", type="warning")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        return
                    resultado: list[EnvioCue | None] = []
                    ok = executar_accion(session, lambda: resultado.append(enviar(
                        session, actor_actual, horta_id, inicio, fin, xeaga, token)))
                if ok:
                    ui.notify("Non hai nada novo que enviar" if not resultado[0] else
                              f"Enviado: {resultado[0].actividades} rexistros")
                    bloque.refresh()

            def saír() -> None:
                desconectar(_id_usuario(), horta_id)
                bloque.refresh()

            with ui.row():
                ui.button("Enviar o pendente", icon="send", on_click=mandar)
                ui.button("Traer o REA", icon="sync",
                          on_click=lambda: _rea(horta_id, xeaga, token)).props("outline")
                ui.button("Desconectar", on_click=saír).props("flat")
        for envio in lista:
            with ui.row().classes("items-center gap-2"):
                ui.label(f"{envio.enviado:%d/%m/%Y %H:%M} · {envio.actividades} rexistros · "
                         f"{_RESULTADOS.get(envio.resultado, envio.resultado)}").classes(
                    "text-body2")
                if envio.resultado == "pendente" and token is not None:
                    ui.button("Comprobar", on_click=partial(_comprobar, envio.id, xeaga,
                                                             token, bloque.refresh)).props(
                        "flat dense")
            if envio.mensaxes:
                ui.label(envio.mensaxes[:300]).classes("texto-suave text-caption")

    bloque()


def _rea(horta_id: int, xeaga: Xeaga, token: Token) -> None:
    """O REA da Xunta fronte aos cultivos da app; nada cambia ata premer «Aceptar»."""
    with get_session() as session:
        actor = usuario_actual(session)
        titular = titular_da_horta(session, horta_id)
        if actor is None or titular is None or not titular.nif:
            return
        try:
            rea = xeaga.exportar_rea(token, titular.nif)
        except XeagaErro as erro:
            ui.notify(str(erro), type="negative")
            return
        comparacion = comparar(session, actor, horta_id, ler_dgcs(rea.rea or []))
    with ui.dialog() as dialogo, ui.card().style("width: min(44rem, 96vw)"):
        ui.label("O REA da Xunta e os cultivos da app").classes("text-h6")
        for e in comparacion.emparellados:
            ui.label(f"{e.texto} → DGC {e.codigo_dgc}").classes("text-body2")
            for diferenza in e.diferenzas:
                ui.label(diferenza).classes("etiqueta-aviso")
        if comparacion.so_na_app:
            ui.label("Só na app (sen recinto no REA): " + ", ".join(comparacion.so_na_app)
                     ).classes("texto-suave")
        if comparacion.so_na_xunta:
            ui.label("Só no REA (falta o cultivo na app): " + ", ".join(
                str(d.codigo) for d in comparacion.so_na_xunta)).classes("texto-suave")

        def aceptar_todo() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is not None and executar_accion(session, lambda: aceptar(
                        session, actor_actual, horta_id, comparacion.emparellados)):
                    ui.notify("Gardado: os envíos levarán as DGC do REA")
                    dialogo.close()

        with ui.row():
            ui.button("Aceptar", icon="check", on_click=aceptar_todo)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")
    dialogo.open()


def _id_usuario() -> int:
    with get_session() as session:
        actor = usuario_actual(session)
        return actor.id if actor else 0


def _comprobar(envio_id: int, xeaga: Xeaga, token: Token, despois: Callable[[], Any]) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        envio = session.get(EnvioCue, envio_id)
        if actor is None or envio is None:
            return
        if executar_accion(session, lambda: comprobar(session, actor, envio, xeaga, token)):
            despois()


def _faltas(horta_id: int, desde: date, ata: date) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            return
        faltas = xerar_cue(session, actor, horta_id, desde, ata).faltas()
    if not faltas:
        ui.label(f"Ao CUE de {desde.year} non lle falta nada.").classes("etiqueta-ok")
        return
    ui.label(f"Que lle falta ao CUE de {desde.year} (non impide descargalo):").classes(
        "text-weight-medium")
    por_traballo: dict[tuple[str, int | None, str], list[str]] = {}
    for falta in faltas:
        chave = (falta.orixe.tipo, falta.orixe.id, falta.orixe.texto)
        por_traballo.setdefault(chave, [])
        if falta.falta not in por_traballo[chave]:
            por_traballo[chave].append(falta.falta)
    with ui.expansion(f"{len(por_traballo)} rexistros con datos que faltan").classes("w-full"):
        for (tipo, _, texto), que in por_traballo.items():
            with ui.row().classes("items-center gap-2 no-wrap"):
                ui.icon("warning").classes("text-warning")
                ui.label(f"{texto}: falta {', '.join(que)}").classes("text-body2")
                if tipo in _SECCION:
                    ui.link("Ver", url_seccion(horta_id, _SECCION[tipo]))
