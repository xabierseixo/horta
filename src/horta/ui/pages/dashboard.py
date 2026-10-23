from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.models.usuario import RolGlobal
from horta.services.animais import listar_animais
from horta.services.hortas import crear_horta, listar_hortas_usuario
from horta.services.parcelas import listar_parcelas
from horta.ui.accions import executar_accion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/")
def dashboard_page() -> None:
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

    if hortas:
        ids = [h.id for h, _ in hortas]
        ultima = app.storage.user.get("ultima_horta")
        destino = ultima if ultima in ids else ids[0]
        ui.navigate.to(f"/hortas/{destino}/resumo")
        return

    cabeceira_paxina(mostrar_admin=e_admin_global)

    with ui.dialog() as dialog_nova_horta, ui.card():
        ui.label("Nova horta").classes("text-md font-bold")
        nome_input = ui.input("Nome")
        profesional_checkbox = ui.checkbox("Uso profesional")

        def crear() -> None:
            if not nome_input.value:
                ui.notify("O nome é obrigatorio", type="negative")
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
                    ),
                )
            if not creada:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Crear", icon="check", on_click=crear)
            ui.button("Cancelar", on_click=dialog_nova_horta.close).props("flat")

    with ui.row().classes("w-full items-center justify-between q-mb-md"):
        ui.label(f"Ola, {nome}").classes("text-xl font-bold")
        ui.button("Nova horta", icon="add", on_click=dialog_nova_horta.open)

    if not hortas:
        ui.label("Aínda non tes ningunha horta.").classes("text-body2")

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
                        ui.badge("profesional").props("color=primary")
                ui.label(f"Rol: {rol.value}").classes("text-caption text-grey")
                ui.label(f"{n_parcelas} parcelas · {n_animais} animais").classes(
                    "text-caption text-grey"
                )
