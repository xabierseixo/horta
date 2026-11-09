from __future__ import annotations

from datetime import datetime

from nicegui import app, ui

from horta.db import get_session
from horta.idiomas import _
from horta.services.auth import autenticar
from horta.services.intentos_login import apuntar_fallo, borrar_fallos, minutos_de_espera
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
        ui.label(_("AgroXest360 — Acceso")).classes("text-xl font-bold")
        email_input = ui.input(_("Email"))
        contrasinal_input = ui.input(_("Contrasinal"), password=True)
        mensaxe_erro = ui.label("").classes("text-negative")

        def tentar_login() -> None:
            agora = datetime.now()
            espera = minutos_de_espera(email_input.value, agora)
            if espera:
                mensaxe_erro.text = _(
                    "Demasiados intentos. Proba de novo dentro de {espera} min"
                ).format(espera=espera)
                return
            with get_session() as session:
                usuario = autenticar(session, email_input.value, contrasinal_input.value)
                if usuario is None:
                    apuntar_fallo(email_input.value, agora)
                    mensaxe_erro.text = _("Email ou contrasinal incorrectos")
                    return
                borrar_fallos(email_input.value)
                app.storage.user["usuario_id"] = usuario.id
                app.storage.user["usuario_nome"] = usuario.nome
                app.storage.user["usuario_rol"] = usuario.rol.value
                app.storage.user["idioma"] = usuario.idioma or "gl"
            ui.navigate.to("/")

        email_input.on("keydown.enter", tentar_login)
        contrasinal_input.on("keydown.enter", tentar_login)
        ui.button(_("Entrar"), on_click=tentar_login)

        with ui.row().classes(
            "texto-suave text-caption q-mt-sm items-center justify-center w-full"
        ):
            ui.link(_("Aviso legal"), "/legal/aviso", new_tab=True).classes(
                "texto-suave text-caption"
            )
            ui.label("·")
            ui.link(_("Política de privacidade"), "/legal/privacidade", new_tab=True).classes(
                "texto-suave text-caption"
            )
