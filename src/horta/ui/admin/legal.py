"""Administración → Datos legais: responsable do tratamento (RGPD/LSSI)."""

from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.models.usuario import RolGlobal, Usuario
from horta.services.legal import gardar_configuracion, ler_configuracion
from horta.ui.accions import executar_accion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/admin/legal")
def admin_legal_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        if actor.rol != RolGlobal.ADMIN:
            cabeceira_paxina()
            ui.label(_("Non tes acceso a esta páxina")).classes("text-negative")
            return
        actor_id = actor.id
        config = ler_configuracion(session)
        nome_val = config.nome if config and config.nome else ""
        nif_val = config.nif if config and config.nif else ""
        enderezo_val = config.enderezo if config and config.enderezo else ""
        correo_val = config.correo if config and config.correo else ""
        dpd_val = config.dpd if config and config.dpd else ""
        localizacion_val = config.localizacion if config and config.localizacion else ""

    cabeceira_paxina(mostrar_admin=True)
    ui.label(_("Datos legais")).classes("text-h6")

    with ui.card().classes("w-full max-w-2xl q-pa-md gap-4"):
        nome_input = ui.input(
            _("Titular do servizo (nome ou razón social)"),
            value=nome_val,
        ).classes("w-full")
        nif_input = ui.input(_("NIF"), value=nif_val).classes("w-full")
        enderezo_input = ui.input(_("Enderezo"), value=enderezo_val).classes("w-full")
        correo_input = ui.input(_("Correo de contacto"), value=correo_val).classes("w-full")
        dpd_input = ui.input(
            _("Delegado de protección de datos (opcional)"),
            value=dpd_val,
        ).classes("w-full")
        localizacion_input = ui.textarea(
            _("Onde se gardan os datos (opcional)"),
            value=localizacion_val,
        ).classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_db = session.get(Usuario, actor_id)
                if actor_db is None:
                    pechar_sesion()
                    return
                feito = executar_accion(
                    session,
                    lambda: gardar_configuracion(
                        session,
                        actor_db,
                        nome=nome_input.value or "",
                        nif=nif_input.value or "",
                        enderezo=enderezo_input.value or "",
                        correo=correo_input.value or "",
                        dpd=dpd_input.value or "",
                        localizacion=localizacion_input.value or "",
                    ),
                )
            if feito:
                ui.notify(_("Datos legais gardados"), type="positive")

        with ui.row().classes("w-full items-center justify-between q-mt-md wrap gap-4"):
            ui.button(_("Gardar"), icon="save", on_click=gardar)
            with ui.row().classes("gap-4"):
                ui.link(_("Ver aviso legal"), "/legal/aviso", new_tab=True)
                ui.link(_("Ver política de privacidade"), "/legal/privacidade", new_tab=True)
