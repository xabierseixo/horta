from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.idiomas import _
from horta.models.usuario import RolGlobal
from horta.services.animais import listar_animais
from horta.services.hortas import crear_horta, listar_hortas_usuario
from horta.services.parcelas import listar_parcelas
from horta.ui.accions import executar_accion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/")
def dashboard_page(nova: bool = False) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        hortas = listar_hortas_usuario(session, actor)
        resumo_hortas = [
            (
                horta,
                rol,
                len(listar_parcelas(session, actor, horta.id)),
                len(listar_animais(session, actor, horta.id)),
            )
            for horta, rol in hortas
        ]
        nome = actor.nome
        e_admin_global = actor.rol == RolGlobal.ADMIN

    if hortas and not nova:
        ids = [h.id for h, _ in hortas]
        ultima = app.storage.user.get("ultima_horta")
        destino = ultima if ultima in ids else ids[0]
        ui.navigate.to(f"/hortas/{destino}/resumo")
        return

    cabeceira_paxina(mostrar_admin=e_admin_global)

    with ui.dialog().props("persistent") as dialog_nova_horta, ui.card():
        ui.label(_("Nova explotación")).classes("text-md font-bold")
        nome_input = ui.input(_("Nome"))
        profesional_checkbox = ui.checkbox(_("Uso profesional"))
        titular_checkbox = ui.checkbox(_("Son a persoa titular da explotación"))

        def crear() -> None:
            if not nome_input.value:
                ui.notify(_("O nome é obrigatorio"), type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                creada = executar_accion(
                    session,
                    lambda: crear_horta(
                        session,
                        actor_actual,
                        nome_input.value,
                        uso_profesional=profesional_checkbox.value,
                        son_titular=titular_checkbox.value,
                    ),
                )
            if not creada:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button(_("Crear"), icon="check", on_click=crear)
            ui.button(_("Cancelar"), on_click=dialog_nova_horta.close).props("flat")

    if nova:
        dialog_nova_horta.open()

    with ui.row().classes("w-full items-center justify-between q-mb-md"):
        ui.label(_("Ola, {nome}").format(nome=nome)).classes("text-xl font-bold")
        ui.button(_("Nova explotación"), icon="add", on_click=dialog_nova_horta.open)

    if not hortas:
        ui.label(_("Aínda non tes ningunha explotación.")).classes("text-body2")

    with ui.row().classes("w-full"):
        for horta, rol, n_parcelas, n_animais in resumo_hortas:
            with (
                ui.card()
                .classes("cursor-pointer")
                .on("click", lambda _, horta_id=horta.id: ui.navigate.to(f"/hortas/{horta_id}"))
            ):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(horta.nome).classes("text-md font-bold")
                    if horta.uso_profesional:
                        ui.badge(_("profesional")).props("color=primary")
                ui.label(_("Rol: {rol}").format(rol=rol.value)).classes("text-caption text-grey")
                ui.label(
                    _("{n_parcelas} parcelas · {n_animais} grupos de animais").format(
                        n_parcelas=n_parcelas, n_animais=n_animais
                    )
                ).classes("text-caption text-grey")
