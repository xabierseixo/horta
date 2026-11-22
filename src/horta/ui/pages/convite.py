"""Abrir un convite (deseño global §2bis): con sesión, entra na explotación coa súa conta; sen
ela, crea a conta co seu propio contrasinal ou entra primeiro coa que xa ten."""

from __future__ import annotations

from nicegui import app, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.persoa import Persoa
from horta.services.equipo import aceptar_convite, convite_valido, crear_conta_con_convite
from horta.services.errors import OperacionNonPermitidaError
from horta.ui.accions import executar_accion
from horta.ui.layout import url_seccion
from horta.ui.sesion import usuario_actual


@ui.page("/convite/{token}")
def convite_page(token: str) -> None:
    with get_session() as session:
        try:
            convite = convite_valido(session, token)
        except OperacionNonPermitidaError as erro:
            ui.label(str(erro)).classes("text-negative q-pa-md")
            return
        horta = session.get(Horta, convite.horta_id)
        persoa = session.get(Persoa, convite.persoa_id)
        actor = usuario_actual(session) if app.storage.user.get("usuario_id") else None
        horta_id, nome_horta = convite.horta_id, horta.nome if horta else ""
        nome_persoa = persoa.nome if persoa else ""

    with ui.card().classes("q-ma-md").style("width: min(28rem, 94vw)"):
        ui.label(f"Convite a «{nome_horta}»").classes("text-h6")
        ui.label(f"Para {nome_persoa}").classes("texto-suave")
        if actor is not None:
            def entrar() -> None:
                with get_session() as session:
                    conta = usuario_actual(session)
                    if conta is None:
                        return
                    ok = executar_accion(session, lambda: aceptar_convite(session, token, conta))
                if ok:
                    ui.navigate.to(url_seccion(horta_id, "resumo"))

            ui.label(f"Entrarás coa túa conta ({actor.email}).")
            ui.button("Entrar na explotación", icon="login", on_click=entrar)
            return

        ui.label("Crea a túa conta: o contrasinal só o sabes ti.")
        email = ui.input("Email").classes("w-full")
        contrasinal = ui.input("Contrasinal (8 caracteres ou máis)", password=True,
                               password_toggle_button=True).classes("w-full")

        def crear() -> None:
            creado: list[tuple[int, str, str]] = []
            with get_session() as session:
                def accion() -> None:
                    u = crear_conta_con_convite(session, token, email.value or "",
                                                contrasinal.value or "")
                    creado.append((u.id, u.nome, u.rol.value))

                ok = executar_accion(session, accion)
            if ok and creado:
                usuario_id, nome, rol = creado[0]
                app.storage.user.update(usuario_id=usuario_id, usuario_nome=nome,
                                        usuario_rol=rol)
                ui.navigate.to(url_seccion(horta_id, "resumo"))

        ui.button("Crear a conta e entrar", icon="person_add", on_click=crear)
        ui.label("Xa tes conta? Entra con ela e volve abrir esta ligazón.").classes(
            "text-caption q-mt-md")
        ui.link("Entrar", "/login")
