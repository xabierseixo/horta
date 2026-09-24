from __future__ import annotations

from nicegui import ui

from horta.db import get_session
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.usuarios import (
    activar_usuario,
    actualizar_usuario,
    crear_usuario,
    desactivar_usuario,
    listar_usuarios,
)
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
    ui.label("Selecciona un usuario na táboa para editalo.").classes("text-caption")
    taboa = ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "email", "label": "Email", "field": "email"},
            {"name": "rol", "label": "Rol", "field": "rol"},
            {"name": "activo", "label": "Activo", "field": "activo"},
        ],
        rows=rows,
        row_key="id",
        selection="single",
    )

    with ui.card().classes("q-mt-md") as tarxeta_edicion:
        titulo_edicion = ui.label("").classes("text-md font-bold")
        nome_edit = ui.input("Nome")
        rol_edit = ui.select(["admin", "usuario"], value="usuario")

        def _usuario_seleccionado_id() -> int | None:
            return taboa.selected[0]["id"] if taboa.selected else None

        def gardar() -> None:
            usuario_id = _usuario_seleccionado_id()
            if usuario_id is None:
                return
            if not nome_edit.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = session.get(Usuario, usuario_id)
                if obxectivo is None:
                    ui.notify("Ese usuario xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_usuario(
                        session,
                        actor_actual,
                        obxectivo,
                        nome=nome_edit.value,
                        rol=RolGlobal(rol_edit.value),
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        def alternar_activo() -> None:
            usuario_id = _usuario_seleccionado_id()
            if usuario_id is None:
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = session.get(Usuario, usuario_id)
                if obxectivo is None:
                    ui.notify("Ese usuario xa non existe", type="negative")
                    return
                accion = desactivar_usuario if obxectivo.activo else activar_usuario
                feito = executar_accion(session, lambda: accion(session, actor_actual, obxectivo))
            if not feito:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar cambios", on_click=gardar)
            boton_activo = ui.button("", on_click=alternar_activo).props("outline")

    def mostrar_edicion() -> None:
        if not taboa.selected:
            tarxeta_edicion.set_visibility(False)
            return
        fila = taboa.selected[0]
        titulo_edicion.text = f"Editar usuario: {fila['email']}"
        nome_edit.value = fila["nome"]
        rol_edit.value = fila["rol"]
        boton_activo.text = "Desactivar" if fila["activo"] == "si" else "Activar"
        tarxeta_edicion.set_visibility(True)

    taboa.on_select(mostrar_edicion)
    tarxeta_edicion.set_visibility(False)

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
