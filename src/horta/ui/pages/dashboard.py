from __future__ import annotations

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta, listar_hortas_usuario


def _actor(session: Session) -> Usuario:
    usuario = session.get(Usuario, app.storage.user["usuario_id"])
    assert usuario is not None
    return usuario


@ui.page("/")
def dashboard_page() -> None:
    with get_session() as session:
        actor = _actor(session)
        hortas = listar_hortas_usuario(session, actor)
        nome = actor.nome
        e_admin_global = actor.rol == RolGlobal.ADMIN

    ui.label(f"Ola, {nome}").classes("text-xl font-bold")

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
                actor_actual = _actor(session)
                crear_horta(
                    session,
                    actor_actual,
                    nome_input.value,
                    uso_profesional=profesional_checkbox.value,
                )
            ui.navigate.reload()

        ui.button("Crear horta", on_click=crear)
