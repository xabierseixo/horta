from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.usuario import RolGlobal
from horta.services.errors import PermisoDenegadoError
from horta.services.usuarios import crear_usuario, listar_usuarios
from horta.ui.accions import executar_accion
from horta.ui.sesion import boton_pechar_sesion, pechar_sesion, usuario_actual


@ui.page("/admin/usuarios")
def admin_usuarios_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            usuarios = listar_usuarios(session, actor)
        except PermisoDenegadoError:
            ui.label("Non tes acceso a esta páxina").classes("text-negative")
            return
        rows = [
            {
                "id": u.id,
                "nome": u.nome,
                "email": u.email,
                "rol": u.rol.value,
                "activo": "si" if u.activo else "non",
            }
            for u in usuarios
        ]

    with ui.row().classes("items-center"):
        ui.link("← As miñas hortas", "/")
        boton_pechar_sesion()

    ui.label("Xestión de usuarios").classes("text-xl font-bold")
    ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "email", "label": "Email", "field": "email"},
            {"name": "rol", "label": "Rol", "field": "rol"},
            {"name": "activo", "label": "Activo", "field": "activo"},
        ],
        rows=rows,
        row_key="id",
    )

    with ui.card().classes("q-mt-md"):
        ui.label("Crear usuario").classes("text-md font-bold")
        nome_input = ui.input("Nome")
        email_input = ui.input("Email")
        contrasinal_input = ui.input("Contrasinal", password=True)
        rol_select = ui.select(["admin", "usuario"], value="usuario")

        def crear() -> None:
            if not (nome_input.value and email_input.value and contrasinal_input.value):
                ui.notify("Todos os campos son obrigatorios", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                creado = executar_accion(
                    session,
                    lambda: crear_usuario(
                        session,
                        actor_actual,
                        nome_input.value,
                        email_input.value,
                        contrasinal_input.value,
                        rol=RolGlobal(rol_select.value),
                    ),
                )
            if not creado:
                return
            ui.navigate.reload()

        ui.button("Crear usuario", on_click=crear)
