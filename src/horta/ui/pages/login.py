from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.services.auth import autenticar


@ui.page("/login")
def login_page() -> None:
    if app.storage.user.get("usuario_id"):
        ui.navigate.to("/")
        return

    with ui.card().classes("absolute-center"):
        ui.label("Horta — Acceso").classes("text-xl font-bold")
        email_input = ui.input("Email")
        contrasinal_input = ui.input("Contrasinal", password=True)
        mensaxe_erro = ui.label("").classes("text-negative")

        def tentar_login() -> None:
            with get_session() as session:
                usuario = autenticar(session, email_input.value, contrasinal_input.value)
                if usuario is None:
                    mensaxe_erro.text = "Email ou contrasinal incorrectos"
                    return
                app.storage.user["usuario_id"] = usuario.id
                app.storage.user["usuario_nome"] = usuario.nome
                app.storage.user["usuario_rol"] = usuario.rol.value
            ui.navigate.to("/")

        ui.button("Entrar", on_click=tentar_login)
