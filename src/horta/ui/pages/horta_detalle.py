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
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual

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

    ui.label(horta_nome).classes("text-2xl font-bold")
    if horta_descricion:
        ui.label(horta_descricion).classes("text-body2")

    if e_horta_admin:
        with ui.expansion("Editar datos da horta").classes("q-mb-md w-full"):
            nome_horta_input = ui.input("Nome", value=horta_nome)
            descricion_horta_input = ui.input("Descrición", value=horta_descricion or "")
            uso_profesional_checkbox = ui.checkbox(
                "Uso profesional", value=horta_uso_profesional
            )

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

            ui.button("Gardar cambios", on_click=gardar_horta)

    # --- Parcelas ---------------------------------------------------------

    ui.label("Parcelas").classes("text-xl font-bold")
    rows = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]
    taboa_parcelas = ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "superficie", "label": "Superficie", "field": "superficie"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows,
        row_key="id",
        selection="single" if pode_editar else None,
    )

    if pode_editar:
        with ui.card().classes("q-mt-md") as tarxeta_edicion_parcela:
            ui.label("Editar parcela").classes("text-md font-bold")
            nome_parcela_edit = ui.input("Nome")
            superficie_parcela_edit = ui.number("Superficie (m²)")
            estado_parcela_edit = ui.input("Estado")

            def _parcela_seleccionada_id() -> int | None:
                if not taboa_parcelas.selected:
                    return None
                return taboa_parcelas.selected[0]["id"]

            def gardar_parcela() -> None:
                parcela_id = _parcela_seleccionada_id()
                if parcela_id is None:
                    return
                if not nome_parcela_edit.value:
                    ui.notify("O nome é obrigatorio", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    parcela_obxectivo = None
                    for p in listar_parcelas(session, actor_actual, horta_id):
                        if p.id == parcela_id:
                            parcela_obxectivo = p
                            break
                    if parcela_obxectivo is None:
                        ui.notify("Esa parcela xa non existe", type="negative")
                        return
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_parcela(
                            session,
                            actor_actual,
                            parcela_obxectivo,
                            nome=nome_parcela_edit.value,
                            superficie=superficie_parcela_edit.value,
                            estado=estado_parcela_edit.value,
                        ),
                    )
                if not gardado:
                    return
                ui.navigate.reload()

            def eliminar_parcela_seleccionada() -> None:
                parcela_id = _parcela_seleccionada_id()
                if parcela_id is None:
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    parcela_obxectivo = None
                    for p in listar_parcelas(session, actor_actual, horta_id):
                        if p.id == parcela_id:
                            parcela_obxectivo = p
                            break
                    if parcela_obxectivo is None:
                        ui.notify("Esa parcela xa non existe", type="negative")
                        return
                    eliminado = executar_accion(
                        session,
                        lambda: eliminar_parcela(session, actor_actual, parcela_obxectivo),
                    )
                if not eliminado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Gardar cambios", on_click=gardar_parcela)
                ui.button("Eliminar", on_click=eliminar_parcela_seleccionada).props(
                    "outline color=negative"
                )

        def mostrar_edicion_parcela() -> None:
            if not taboa_parcelas.selected:
                tarxeta_edicion_parcela.set_visibility(False)
                return
            fila = taboa_parcelas.selected[0]
            nome_parcela_edit.value = fila["nome"]
            superficie_parcela_edit.value = fila["superficie"]
            estado_parcela_edit.value = fila["estado"]
            tarxeta_edicion_parcela.set_visibility(True)

        taboa_parcelas.on_select(mostrar_edicion_parcela)
        tarxeta_edicion_parcela.set_visibility(False)

        with ui.card().classes("q-mt-md"):
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

            ui.button("Crear parcela", on_click=crear)

    # --- Animais ------------------------------------------------------------

    ui.label("Animais").classes("text-xl font-bold").classes("q-mt-lg")
    rows_animais = [
        {
            "id": a.id,
            "especie": a.especie,
            "raza": a.raza,
            "cantidade": a.cantidade,
            "estado": a.estado,
        }
        for a in animais
    ]
    taboa_animais = ui.table(
        columns=[
            {"name": "especie", "label": "Especie", "field": "especie"},
            {"name": "raza", "label": "Raza", "field": "raza"},
            {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows_animais,
        row_key="id",
        selection="single" if pode_editar else None,
    )

    if pode_editar:
        with ui.card().classes("q-mt-md") as tarxeta_edicion_animal:
            ui.label("Editar animal").classes("text-md font-bold")
            especie_animal_edit = ui.input("Especie")
            raza_animal_edit = ui.input("Raza")
            cantidade_animal_edit = ui.number("Cantidade")
            estado_animal_edit = ui.input("Estado")

            def _animal_seleccionado_id() -> int | None:
                if not taboa_animais.selected:
                    return None
                return taboa_animais.selected[0]["id"]

            def gardar_animal() -> None:
                animal_id = _animal_seleccionado_id()
                if animal_id is None:
                    return
                if not especie_animal_edit.value:
                    ui.notify("A especie é obrigatoria", type="negative")
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    animal_obxectivo = None
                    for a in listar_animais(session, actor_actual, horta_id):
                        if a.id == animal_id:
                            animal_obxectivo = a
                            break
                    if animal_obxectivo is None:
                        ui.notify("Ese animal xa non existe", type="negative")
                        return
                    gardado = executar_accion(
                        session,
                        lambda: actualizar_animal(
                            session,
                            actor_actual,
                            animal_obxectivo,
                            especie=especie_animal_edit.value,
                            raza=raza_animal_edit.value or None,
                            cantidade=int(cantidade_animal_edit.value or 1),
                            estado=estado_animal_edit.value,
                        ),
                    )
                if not gardado:
                    return
                ui.navigate.reload()

            def eliminar_animal_seleccionado() -> None:
                animal_id = _animal_seleccionado_id()
                if animal_id is None:
                    return
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    animal_obxectivo = None
                    for a in listar_animais(session, actor_actual, horta_id):
                        if a.id == animal_id:
                            animal_obxectivo = a
                            break
                    if animal_obxectivo is None:
                        ui.notify("Ese animal xa non existe", type="negative")
                        return
                    eliminado = executar_accion(
                        session,
                        lambda: eliminar_animal(session, actor_actual, animal_obxectivo),
                    )
                if not eliminado:
                    return
                ui.navigate.reload()

            with ui.row():
                ui.button("Gardar cambios", on_click=gardar_animal)
                ui.button("Eliminar", on_click=eliminar_animal_seleccionado).props(
                    "outline color=negative"
                )

        def mostrar_edicion_animal() -> None:
            if not taboa_animais.selected:
                tarxeta_edicion_animal.set_visibility(False)
                return
            fila = taboa_animais.selected[0]
            especie_animal_edit.value = fila["especie"]
            raza_animal_edit.value = fila["raza"]
            cantidade_animal_edit.value = fila["cantidade"]
            estado_animal_edit.value = fila["estado"]
            tarxeta_edicion_animal.set_visibility(True)

        taboa_animais.on_select(mostrar_edicion_animal)
        tarxeta_edicion_animal.set_visibility(False)

        with ui.card().classes("q-mt-md"):
            ui.label("Novo animal").classes("text-md font-bold")
            especie_input = ui.input("Especie (p.ex. galiñas, coellos)")
            raza_input = ui.input("Raza (opcional)")
            cantidade_input = ui.number("Cantidade", value=1)

            def crear_animal_novo() -> None:
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

            ui.button("Crear animal", on_click=crear_animal_novo)

    # --- Membros --------------------------------------------------------

    if e_horta_admin:
        with ui.card().classes("q-mt-md"):
            ui.label("Membros da horta").classes("text-md font-bold")

            with get_session() as session:
                membros_bd = session.query(HortaMembro).filter_by(horta_id=horta_id).all()
                filas_membros = []
                for m in membros_bd:
                    usuario_membro = session.get(Usuario, m.usuario_id)
                    assert usuario_membro is not None
                    filas_membros.append(
                        {
                            "usuario_id": m.usuario_id,
                            "nome": usuario_membro.nome,
                            "email": usuario_membro.email,
                            "rol": m.rol.value,
                        }
                    )

            ui.label("Selecciona un membro para cambiar o seu rol ou quitalo.").classes(
                "text-caption"
            )
            taboa_membros = ui.table(
                columns=[
                    {"name": "nome", "label": "Nome", "field": "nome"},
                    {"name": "email", "label": "Email", "field": "email"},
                    {"name": "rol", "label": "Rol", "field": "rol"},
                ],
                rows=filas_membros,
                row_key="usuario_id",
                selection="single",
            )

            with ui.row().classes("items-center") as fila_edicion_membro:
                titulo_membro = ui.label("")
                rol_membro_edit = ui.select(["admin", "editor", "lector"], value="lector")

                def _membro_seleccionado_id() -> int | None:
                    if not taboa_membros.selected:
                        return None
                    return taboa_membros.selected[0]["usuario_id"]

                def cambiar_rol() -> None:
                    usuario_obxectivo_id = _membro_seleccionado_id()
                    if usuario_obxectivo_id is None:
                        return
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
                                RolHorta(rol_membro_edit.value),
                            ),
                        )
                    if not cambiado:
                        return
                    ui.navigate.reload()

                def quitar() -> None:
                    usuario_obxectivo_id = _membro_seleccionado_id()
                    if usuario_obxectivo_id is None:
                        return
                    with get_session() as session:
                        actor_actual = usuario_actual(session)
                        if actor_actual is None:
                            pechar_sesion()
                            return
                        quitouse_a_si_mesmo = usuario_obxectivo_id == actor_actual.id
                        quitado = executar_accion(
                            session,
                            lambda: quitar_membro(
                                session, actor_actual, horta_id, usuario_obxectivo_id
                            ),
                        )
                    if not quitado:
                        return
                    if quitouse_a_si_mesmo:
                        ui.navigate.to("/")
                    else:
                        ui.navigate.reload()

                ui.button("Cambiar rol", on_click=cambiar_rol)
                ui.button("Quitar da horta", on_click=quitar).props("outline color=negative")

            def mostrar_edicion_membro() -> None:
                if not taboa_membros.selected:
                    fila_edicion_membro.set_visibility(False)
                    return
                fila = taboa_membros.selected[0]
                titulo_membro.text = f"{fila['nome']} ({fila['email']})"
                rol_membro_edit.value = fila["rol"]
                fila_edicion_membro.set_visibility(True)

            taboa_membros.on_select(mostrar_edicion_membro)
            fila_edicion_membro.set_visibility(False)

            ui.separator()
            email_novo_membro = ui.input("Email do usuario a engadir")
            rol_novo_membro = ui.select(["admin", "editor", "lector"], value="lector")

            def engadir() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    usuario_obxectivo = (
                        session.query(Usuario)
                        .filter_by(email=email_novo_membro.value)
                        .one_or_none()
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
                            RolHorta(rol_novo_membro.value),
                        ),
                    )
                if not engadido:
                    return
                ui.navigate.reload()

            ui.button("Engadir membro", on_click=engadir)
