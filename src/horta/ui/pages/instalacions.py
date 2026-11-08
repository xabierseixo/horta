"""Sección Instalacións (paso 14): almacéns, galiñeiros, cortes, invernadoiros…"""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.models.instalacion import Instalacion
from horta.services.errors import OperacionNonPermitidaError
from horta.services.instalacions import (
    TIPOS_INSTALACION,
    actualizar_instalacion,
    crear_instalacion,
    listar_instalacions,
)
from horta.ui.accions import executar_accion
from horta.ui.historial import abrir_historial
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_instalacions(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        instalacions = listar_instalacions(session, actor, horta_id)
    por_id = {i.id: i for i in instalacions}
    taboa = ui.table(
        columns=[{"name": k, "label": e, "field": k, "align": "left"} for k, e in (
            ("nome", "Nome"), ("tipo", "Tipo"), ("enderezo", "Enderezo"),
            ("catastro", "Ref. catastral"), ("estado", "Estado"))],
        rows=[{"id": i.id, "nome": i.nome, "tipo": TIPOS_INSTALACION[i.tipo],
               "enderezo": i.enderezo or "", "catastro": i.referencia_catastral or "",
               "estado": "En uso" if i.activa else "Sen uso"} for i in instalacions],
        row_key="id", selection="single",
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai instalacións" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "nome", ["tipo", "estado"], accions_tarxeta)

    def escollida() -> int | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha instalación na táboa", type="warning")
            return None
        return int(taboa.selected[0]["id"])

    def historial() -> None:
        if (i := escollida()) is not None:
            abrir_historial("instalacion", i)

    editar: Callable[[], None] | None = None
    with ui.row():
        if pode_editar:
            editando: dict[str, int | None] = {"id": None}
            with (ui.dialog().props("persistent") as dialogo,
                  ui.card().style("width: min(30rem, 94vw)")):
                titulo = ui.label("").classes("text-h6")
                nome = ui.input("Nome (p.ex. Galiñeiro de abaixo)").classes("w-full")
                tipo = ui.select(TIPOS_INSTALACION, label="Tipo").classes("w-full")
                enderezo = ui.input("Enderezo").classes("w-full")
                catastro = ui.input("Referencia catastral").classes("w-full")
                activa = ui.checkbox("En uso", value=True)
                notas = ui.textarea("Notas").classes("w-full")

                def gardar() -> None:
                    with get_session() as session:
                        actor_actual = usuario_actual(session)
                        if actor_actual is None:
                            pechar_sesion()
                            return
                        campos = {"enderezo": enderezo.value or None,
                                  "referencia_catastral": catastro.value or None,
                                  "notas": notas.value or None, "activa": activa.value}

                        def accion() -> None:
                            if tipo.value is None:
                                raise OperacionNonPermitidaError("Escolle o tipo")
                            existente = (session.get(Instalacion, editando["id"])
                                         if editando["id"] else None)
                            if existente is None:
                                crear_instalacion(session, actor_actual, horta_id, tipo.value,
                                                  nome.value or "", **campos)
                            else:
                                actualizar_instalacion(session, actor_actual, existente,
                                                       tipo=tipo.value, nome=nome.value or "",
                                                       **campos)

                        ok = executar_accion(session, accion)
                    if ok:
                        ui.navigate.reload()

                with ui.row():
                    ui.button("Gardar", icon="check", on_click=gardar)
                    ui.button("Cancelar", on_click=dialogo.close).props("flat")

            def abrir(instalacion: Instalacion | None) -> None:
                editando["id"] = instalacion.id if instalacion else None
                titulo.text = "Editar instalación" if instalacion else "Nova instalación"
                nome.value = instalacion.nome if instalacion else ""
                tipo.value = instalacion.tipo if instalacion else None
                enderezo.value = (instalacion.enderezo or "") if instalacion else ""
                catastro.value = (instalacion.referencia_catastral or "") if instalacion else ""
                activa.value = instalacion.activa if instalacion else True
                notas.value = (instalacion.notas or "") if instalacion else ""
                dialogo.open()

            def editar() -> None:
                if (i := escollida()) is not None:
                    abrir(por_id[i])

            accions_tarxeta.append(("Editar", "edit", editar))
            ui.button("Nova instalación", icon="add", on_click=lambda: abrir(None))

        accions_tarxeta.append(("Historial", "history", historial))
        with ui.row().classes("so-ordenador"):
            if editar is not None:
                ui.button("Editar", icon="edit", on_click=editar).props("outline")
            ui.button("Historial", icon="history", on_click=historial).props("outline")
