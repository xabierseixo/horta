from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.services.auth import autenticar
from horta.ui.nav import aplicar_paleta
from horta.ui.sesion import usuario_actual


@ui.page("/login")
def login_page() -> None:
    aplicar_paleta()
    if app.storage.user.get("usuario_id"):
        with get_session() as session:
            sesion_valida = usuario_actual(session) is not None
        if sesion_valida:
            ui.navigate.to("/")
            return
        app.storage.user.clear()

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
