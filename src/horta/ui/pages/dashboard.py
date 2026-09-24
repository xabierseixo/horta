from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.usuario import RolGlobal
from horta.services.hortas import crear_horta, listar_hortas_usuario
from horta.ui.sesion import boton_pechar_sesion, pechar_sesion, usuario_actual


@ui.page("/")
def dashboard_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        hortas = listar_hortas_usuario(session, actor)
        nome = actor.nome
        e_admin_global = actor.rol == RolGlobal.ADMIN

    with ui.row().classes("items-center"):
        ui.label(f"Ola, {nome}").classes("text-xl font-bold")
        boton_pechar_sesion()

    if e_admin_global:
        ui.link("Administración de usuarios", "/admin/usuarios")

    ui.label("As túas hortas").classes("text-lg font-bold").classes("q-mt-md")

    if not hortas:
        ui.label("Aínda non tes ningunha horta.")
    for horta, rol in hortas:
        with ui.row().classes("items-center"):
            ui.link(horta.nome, f"/hortas/{horta.id}")
            ui.label(f"({rol.value})")

    with ui.card().classes("q-mt-md"):
        ui.label("Crear nova horta").classes("text-md font-bold")
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
                crear_horta(
                    session,
                    actor_actual,
                    nome_input.value,
                    uso_profesional=profesional_checkbox.value,
                )
            ui.navigate.reload()

        ui.button("Crear horta", on_click=crear)
