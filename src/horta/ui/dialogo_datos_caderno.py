"""Diálogo «Datos do caderno»: enderezo e asesoramento (modelo da Xunta, 1.1 e 1.4)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.services.hortas import TIPOS_XIP, actualizar_horta
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual

_TEXTOS = (("enderezo", "Enderezo"), ("localidade", "Localidade"),
           ("codigo_postal", "Código postal"), ("provincia", "Provincia"), ("email", "Email"),
           ("tipo_representacion", "Tipo de representación (se asina un representante)"))
_ASESORAMENTO = (("asesoramento_nome", "Entidade ou agrupación de asesoramento"),
                 ("asesoramento_nif", "NIF da entidade"),
                 ("asesoramento_num", "Nº de identificación"))


def boton_datos_caderno(horta_id: int) -> None:
    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        ui.label("Datos do caderno").classes("text-h6")
        ui.label("Saen na primeira folla do caderno de explotación.").classes("text-caption")
        campos = {campo: ui.input(etiqueta).classes("w-full") for campo, etiqueta in _TEXTOS}
        ui.label("Asesoramento en xestión integrada de pragas").classes("text-subtitle2")
        tipo_xip = ui.select(TIPOS_XIP, label="Tipo de explotación", clearable=True).classes(
            "w-full")
        campos |= {campo: ui.input(etiqueta).classes("w-full")
                   for campo, etiqueta in _ASESORAMENTO}
        fertilizacion = ui.checkbox("Recibe asesoramento en fertilización")

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                horta = session.get(Horta, horta_id)
                if actor is None or horta is None:
                    pechar_sesion()
                    return
                cambios = {c: (i.value or None) for c, i in campos.items()}
                ok = executar_accion(session, lambda: actualizar_horta(
                    session, actor, horta, tipo_xip=tipo_xip.value,
                    asesoramento_fertilizacion=fertilizacion.value, **cambios))
            if ok:
                ui.notify("Gardado", type="positive")
                dialogo.close()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        with get_session() as session:
            horta = session.get(Horta, horta_id)
        if horta is None:
            return
        for campo, entrada in campos.items():
            entrada.value = getattr(horta, campo) or ""
        tipo_xip.value = horta.tipo_xip
        fertilizacion.value = horta.asesoramento_fertilizacion
        dialogo.open()

    ui.button("Datos do caderno", icon="badge", on_click=abrir).props("outline")
