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
from horta.ui.filtros import filtrar_filas
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual

_PROPS_TABOA = 'dense no-data-label="Non hai usuarios"'

_ROLES_USUARIO = ("admin", "usuario")


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
            cabeceira_paxina()
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

    cabeceira_paxina(mostrar_admin=True)

    with ui.dialog() as dialog_crear, ui.card():
        ui.label("Crear usuario").classes("text-md font-bold")
        nome_input = ui.input("Nome")
        email_input = ui.input("Email")
        contrasinal_input = ui.input("Contrasinal", password=True)
        rol_select = ui.select(list(_ROLES_USUARIO), value="usuario")

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

        with ui.row():
            ui.button("Crear", icon="check", on_click=crear)
            ui.button("Cancelar", on_click=dialog_crear.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Xestión de usuarios").classes("text-xl font-bold")
        ui.button("Crear usuario", icon="person_add", on_click=dialog_crear.open)

    ui.label("Selecciona un usuario na táboa para editalo.").classes("text-caption")

    with ui.row().classes("w-full items-center q-gutter-sm q-mb-sm"):
        busca_input = ui.input("Buscar").props("dense clearable")
        rol_filtro_select = ui.select(
            ["Todos", *_ROLES_USUARIO], label="Rol", value="Todos"
        ).props("dense")
        activo_select = ui.select(
            ["Todos", "si", "non"], label="Activo", value="Todos"
        ).props("dense")

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
                {"name": "activo", "label": "Activo", "field": "activo"},
            ],
            rows=rows,
            row_key="id",
            selection="single",
            pagination=10,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    def refrescar_taboa() -> None:
        rol_filtro = None if rol_filtro_select.value == "Todos" else rol_filtro_select.value
        activo_filtro = None if activo_select.value == "Todos" else activo_select.value
        taboa.rows = filtrar_filas(
            rows,
            busca_input.value or "",
            ["nome", "email", "rol", "activo"],
            {"rol": rol_filtro, "activo": activo_filtro},
        )
        if taboa.selected and taboa.selected[0] not in taboa.rows:
            taboa.selected = []
            fila_accions.set_visibility(False)
        taboa.update()

    busca_input.on_value_change(refrescar_taboa)
    rol_filtro_select.on_value_change(refrescar_taboa)
    activo_select.on_value_change(refrescar_taboa)

    with ui.dialog() as dialog_editar, ui.card():
        titulo_edicion = ui.label("").classes("text-md font-bold")
        nome_edit = ui.input("Nome")
        rol_edit = ui.select(list(_ROLES_USUARIO), value="usuario")

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
            ui.button("Gardar cambios", icon="check", on_click=gardar)
            boton_activo = ui.button("", on_click=alternar_activo).props("outline")
            ui.button("Cerrar", on_click=dialog_editar.close).props("flat")

    def abrir_edicion() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        titulo_edicion.text = f"Editar usuario: {fila['email']}"
        nome_edit.value = fila["nome"]
        rol_edit.value = fila["rol"]
        boton_activo.text = "Desactivar" if fila["activo"] == "si" else "Activar"
        boton_activo.props(f"icon={'block' if fila['activo'] == 'si' else 'check_circle'}")
        dialog_editar.open()

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=abrir_edicion)
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))
