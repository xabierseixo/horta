from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import (
    actualizar_horta,
    cambiar_rol_membro,
    comprobar_rol_horta,
    engadir_membro,
    quitar_membro,
)
from horta.services.parcelas import (
    actualizar_parcela,
    crear_parcela,
    eliminar_parcela,
    listar_parcelas,
)
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual

_PROPS_TABOA = 'dense no-data-label="Non hai rexistros"'

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@ui.page("/hortas/{horta_id}")
def horta_detalle_page(horta_id: int) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
        except PermisoDenegadoError:
            cabeceira_paxina()
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        horta = session.get(Horta, horta_id)
        assert horta is not None
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA
        e_horta_admin = membro.rol == RolHorta.ADMIN
        e_admin_global = actor.rol == RolGlobal.ADMIN
        horta_nome = horta.nome
        horta_descricion = horta.descricion
        horta_uso_profesional = horta.uso_profesional

    cabeceira_paxina(titulo_horta=horta_nome, mostrar_admin=e_admin_global)

    if e_horta_admin:
        with ui.dialog() as dialog_config_horta, ui.card():
            ui.label("Configurar horta").classes("text-md font-bold")
            nome_horta_input = ui.input("Nome", value=horta_nome)
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "")
            uso_profesional_checkbox = ui.checkbox("Uso profesional", value=horta_uso_profesional)

            def gardar_horta() -> None:
                if not nome_horta_input.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    horta_obxectivo = session.get(Horta, horta_id)
                    if horta_obxectivo is None:
                        ui.notify("Esta horta xa non existe", type="negative")
                        return
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_horta(
                            session,
                            actor_actual,
                            horta_obxectivo,
                            nome=nome_horta_input.value,
                            descricion=descricion_horta_input.value or None,
                            uso_profesional=uso_profesional_checkbox.value,
                        ),
                    )
                if not gardado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar_horta)
                ui.button("Cancelar", on_click=dialog_config_horta.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        with ui.column().classes("gap-0"):
            ui.label(horta_nome).classes("text-2xl font-bold")
            if horta_descricion:
                ui.label(horta_descricion).classes("text-body2 text-grey")
        if e_horta_admin:
            ui.button("Configurar horta", icon="settings", on_click=dialog_config_horta.open).props(
                "outline"
            )

    with ui.tabs().classes("w-full q-mt-md") as pestanas:
        pestana_parcelas = ui.tab("Parcelas")
        pestana_animais = ui.tab("Animais")
        if e_horta_admin:
            pestana_membros = ui.tab("Membros")

    with ui.tab_panels(pestanas, value=pestana_parcelas).classes("w-full"):
        with ui.tab_panel(pestana_parcelas):
            _seccion_parcelas(horta_id, parcelas, pode_editar)
        with ui.tab_panel(pestana_animais):
            _seccion_animais(horta_id, animais, pode_editar)
        if e_horta_admin:
            with ui.tab_panel(pestana_membros):
                _seccion_membros(horta_id)


def _seccion_parcelas(horta_id: int, parcelas: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_nova_parcela, ui.card():
            ui.label("Nova parcela").classes("text-md font-bold")
            nome_input = ui.input("Nome")
            superficie_input = ui.number("Superficie (m²)")

            def crear() -> None:
                if not nome_input.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creada = executar_accion(
                        session,
                        lambda: crear_parcela(
                            session,
                            actor_actual,
                            horta_id,
                            nome_input.value,
                            superficie=superficie_input.value,
                        ),
                    )
                if not creada:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_nova_parcela.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Parcelas").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Nova parcela", icon="add", on_click=dialog_nova_parcela.open)

    rows = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]
    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "superficie", "label": "Superficie", "field": "superficie"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=rows,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f"Eliminar a parcela «{taboa.selected[0]['nome']}»? Non se pode desfacer.",
                eliminar_seleccionada,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar parcela").classes("text-md font-bold")
        nome_edit = ui.input("Nome")
        superficie_edit = ui.number("Superficie (m²)")
        estado_edit = ui.input("Estado")

        def gardar() -> None:
            if not taboa.selected:
                return
            parcela_id = taboa.selected[0]["id"]
            if not nome_edit.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        p
                        for p in listar_parcelas(session, actor_actual, horta_id)
                        if p.id == parcela_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Esa parcela xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_parcela(
                        session,
                        actor_actual,
                        obxectivo,
                        nome=nome_edit.value,
                        superficie=superficie_edit.value,
                        estado=estado_edit.value,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        nome_edit.value = fila["nome"]
        superficie_edit.value = fila["superficie"]
        estado_edit.value = fila["estado"]
        dialog_editar.open()

    def eliminar_seleccionada() -> None:
        if not taboa.selected:
            return
        parcela_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (p for p in listar_parcelas(session, actor_actual, horta_id) if p.id == parcela_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Esa parcela xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_parcela(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_animais(horta_id: int, animais: list, pode_editar: bool) -> None:
    if pode_editar:
        with ui.dialog() as dialog_novo_animal, ui.card():
            ui.label("Novo animal").classes("text-md font-bold")
            especie_input = ui.input("Especie (p.ex. galiñas, coellos)")
            raza_input = ui.input("Raza (opcional)")
            cantidade_input = ui.number("Cantidade", value=1)

            def crear() -> None:
                if not especie_input.value:
                    ui.notify("A especie é obrigatoria", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    creado = executar_accion(
                        session,
                        lambda: crear_animal(
                            session,
                            actor_actual,
                            horta_id,
                            especie_input.value,
                            date.today(),
                            raza=raza_input.value or None,
                            cantidade=int(cantidade_input.value or 1),
                        ),
                    )
                if not creado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Crear", icon="check", on_click=crear)
                ui.button("Cancelar", on_click=dialog_novo_animal.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Animais").classes("text-lg font-bold")
        if pode_editar:
            ui.button("Novo animal", icon="add", on_click=dialog_novo_animal.open)

    rows = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]
    taboa = (
        ui.table(
            columns=[
                {"name": "especie", "label": "Especie", "field": "especie"},
                {"name": "raza", "label": "Raza", "field": "raza"},
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
            ],
            rows=rows,
            row_key="id",
            selection="single" if pode_editar else None,
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    if not pode_editar:
        return

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Editar", icon="edit", on_click=lambda: abrir_editar())
        ui.button(
            "Eliminar",
            icon="delete",
            on_click=lambda: confirmar_eliminacion(
                f'Eliminar "{taboa.selected[0]["especie"]}"? Esta acción non se pode desfacer.',
                eliminar_seleccionado,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_editar, ui.card():
        ui.label("Editar animal").classes("text-md font-bold")
        especie_edit = ui.input("Especie")
        raza_edit = ui.input("Raza")
        cantidade_edit = ui.number("Cantidade")
        estado_edit = ui.input("Estado")

        def gardar() -> None:
            if not taboa.selected:
                return
            animal_id = taboa.selected[0]["id"]
            if not especie_edit.value:
                ui.notify("A especie é obrigatoria", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                obxectivo = next(
                    (
                        a
                        for a in listar_animais(session, actor_actual, horta_id)
                        if a.id == animal_id
                    ),
                    None,
                )
                if obxectivo is None:
                    ui.notify("Ese animal xa non existe", type="negative")
                    return
                gardado = executar_accion(
                    session,
                    lambda: actualizar_animal(
                        session,
                        actor_actual,
                        obxectivo,
                        especie=especie_edit.value,
                        raza=raza_edit.value or None,
                        cantidade=int(cantidade_edit.value or 1),
                        estado=estado_edit.value,
                    ),
                )
            if not gardado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialog_editar.close).props("flat")

    def abrir_editar() -> None:
        if not taboa.selected:
            return
        fila = taboa.selected[0]
        especie_edit.value = fila["especie"]
        raza_edit.value = fila["raza"]
        cantidade_edit.value = fila["cantidade"]
        estado_edit.value = fila["estado"]
        dialog_editar.open()

    def eliminar_seleccionado() -> None:
        if not taboa.selected:
            return
        animal_id = taboa.selected[0]["id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            obxectivo = next(
                (a for a in listar_animais(session, actor_actual, horta_id) if a.id == animal_id),
                None,
            )
            if obxectivo is None:
                ui.notify("Ese animal xa non existe", type="negative")
                return
            eliminado = executar_accion(
                session, lambda: eliminar_animal(session, actor_actual, obxectivo)
            )
        if not eliminado:
            return
        ui.navigate.reload()


def _seccion_membros(horta_id: int) -> None:
    with get_session() as session:
        membros_bd = session.query(HortaMembro).filter_by(horta_id=horta_id).all()
        filas = []
        for m in membros_bd:
            usuario_membro = session.get(Usuario, m.usuario_id)
            assert usuario_membro is not None
            filas.append(
                {
                    "usuario_id": m.usuario_id,
                    "nome": usuario_membro.nome,
                    "email": usuario_membro.email,
                    "rol": m.rol.value,
                }
            )

    with ui.dialog() as dialog_engadir, ui.card():
        ui.label("Engadir membro").classes("text-md font-bold")
        email_input = ui.input("Email do usuario")
        rol_input = ui.select(["admin", "editor", "lector"], value="lector")

        def engadir() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                usuario_obxectivo = (
                    session.query(Usuario).filter_by(email=email_input.value).one_or_none()
                )
                if usuario_obxectivo is None:
                    ui.notify("Non existe ningún usuario con ese email", type="negative")
                    return
                engadido = executar_accion(
                    session,
                    lambda: engadir_membro(
                        session,
                        actor_actual,
                        horta_id,
                        usuario_obxectivo,
                        RolHorta(rol_input.value),
                    ),
                )
            if not engadido:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Engadir", icon="check", on_click=engadir)
            ui.button("Cancelar", on_click=dialog_engadir.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
        ui.label("Membros").classes("text-lg font-bold")
        ui.button("Engadir membro", icon="person_add", on_click=dialog_engadir.open)

    taboa = (
        ui.table(
            columns=[
                {"name": "nome", "label": "Nome", "field": "nome"},
                {"name": "email", "label": "Email", "field": "email"},
                {"name": "rol", "label": "Rol", "field": "rol"},
            ],
            rows=filas,
            row_key="usuario_id",
            selection="single",
        )
        .classes("w-full")
        .props(_PROPS_TABOA)
    )

    with ui.row().classes("q-mt-sm") as fila_accions:
        ui.button("Cambiar rol", icon="edit", on_click=lambda: abrir_cambiar_rol())
        ui.button(
            "Quitar da horta",
            icon="person_remove",
            on_click=lambda: confirmar_eliminacion(
                f'Quitar a "{taboa.selected[0]["nome"]}" desta horta?',
                quitar,
            ),
        ).props("outline color=negative")
    fila_accions.set_visibility(False)
    taboa.on_select(lambda: fila_accions.set_visibility(bool(taboa.selected)))

    with ui.dialog() as dialog_cambiar_rol, ui.card():
        ui.label("Cambiar rol do membro").classes("text-md font-bold")
        rol_edit = ui.select(["admin", "editor", "lector"], value="lector")

        def cambiar_rol() -> None:
            if not taboa.selected:
                return
            usuario_obxectivo_id = taboa.selected[0]["usuario_id"]
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                cambiado = executar_accion(
                    session,
                    lambda: cambiar_rol_membro(
                        session,
                        actor_actual,
                        horta_id,
                        usuario_obxectivo_id,
                        RolHorta(rol_edit.value),
                    ),
                )
            if not cambiado:
                return
            ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=cambiar_rol)
            ui.button("Cancelar", on_click=dialog_cambiar_rol.close).props("flat")

    def abrir_cambiar_rol() -> None:
        if not taboa.selected:
            return
        rol_edit.value = taboa.selected[0]["rol"]
        dialog_cambiar_rol.open()

    def quitar() -> None:
        if not taboa.selected:
            return
        usuario_obxectivo_id = taboa.selected[0]["usuario_id"]
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            quitouse_a_si_mesmo = usuario_obxectivo_id == actor_actual.id
            quitado = executar_accion(
                session,
                lambda: quitar_membro(session, actor_actual, horta_id, usuario_obxectivo_id),
            )
        if not quitado:
            return
        if quitouse_a_si_mesmo:
            ui.navigate.to("/")
        else:
            ui.navigate.reload()
