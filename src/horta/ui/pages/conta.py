"""Páxina de xestión da conta de usuario e dereitos RGPD."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.legal import borrar_minha_conta, exportar_meus_datos
from horta.ui.accions import executar_accion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual


@ui.page("/conta")
def conta_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        actor_id = actor.id
        nome = actor.nome
        email = actor.email
        e_admin_global = actor.rol == RolGlobal.ADMIN
        data_politica = (
            f"Política aceptada o {actor.politica_aceptada_en:%d/%m/%Y}"
            if actor.politica_aceptada_en
            else "Política pendente de aceptación"
        )

    cabeceira_paxina(mostrar_admin=e_admin_global)
    ui.label("A miña conta").classes("text-h6")

    def descargar_datos() -> None:
        with get_session() as session:
            actor_db = session.get(Usuario, actor_id)
            if actor_db is None:
                pechar_sesion()
                return
            contido = exportar_meus_datos(session, actor_db)
        ui.download.content(contido, "os-meus-datos.json")

    with ui.dialog() as dialog_borrar, ui.card().classes("w-full max-w-md"):
        ui.label("Borrar a miña conta").classes("text-h6 text-negative")
        ui.label(
            "A conta queda borrada e non poderás entrar máis. "
            "Os rexistros obrigatorios das explotacións consérvanse, como esixe a normativa."
        )
        campo_confirmar = ui.input(placeholder="BORRAR").classes("w-full")

        def confirmar_borrado() -> None:
            with get_session() as session:
                actor_db = session.get(Usuario, actor_id)
                if actor_db is None:
                    pechar_sesion()
                    return
                feito = executar_accion(
                    session, lambda: borrar_minha_conta(session, actor_db)
                )
            if feito:
                dialog_borrar.close()
                pechar_sesion()

        with ui.row().classes("justify-end gap-2 w-full q-mt-md"):
            ui.button("Cancelar", on_click=dialog_borrar.close).props("flat")
            boton_confirmar = ui.button(
                "Borrar a miña conta",
                icon="delete_forever",
                on_click=confirmar_borrado,
            ).props("color=negative")
            boton_confirmar.disable()

        def ao_escribir(e: Any) -> None:
            if (e.value or "").strip() == "BORRAR":
                boton_confirmar.enable()
            else:
                boton_confirmar.disable()

        campo_confirmar.on_value_change(ao_escribir)

    def abrir_dialogo_borrar() -> None:
        campo_confirmar.value = ""
        boton_confirmar.disable()
        dialog_borrar.open()

    with ui.card().classes("w-full max-w-xl q-pa-md gap-3"):
        ui.label(nome).classes("text-subtitle1 text-weight-bold")
        ui.label(email).classes("texto-suave")
        ui.label(data_politica).classes("texto-suave")

        with ui.row().classes("gap-4 q-my-sm"):
            ui.link("Aviso legal", "/legal/aviso", new_tab=True)
            ui.link("Política de privacidade", "/legal/privacidade", new_tab=True)

        with ui.row().classes("gap-3 q-mt-md wrap"):
            ui.button(
                "Descargar os meus datos",
                icon="download",
                on_click=descargar_datos,
            ).props("outline")
            ui.button(
                "Borrar a miña conta",
                icon="delete",
                on_click=abrir_dialogo_borrar,
            ).props("color=negative")
