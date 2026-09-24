from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.horta import HortaMembro, RolHorta
from horta.models.usuario import Usuario
from horta.services.animais import crear_animal, listar_animais
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import (
    cambiar_rol_membro,
    comprobar_rol_horta,
    engadir_membro,
    quitar_membro,
)
from horta.services.parcelas import crear_parcela, listar_parcelas
from horta.ui.accions import executar_accion
from horta.ui.sesion import boton_pechar_sesion, pechar_sesion, usuario_actual

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
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA

    with ui.row().classes("items-center"):
        ui.link("← As miñas hortas", "/")
        boton_pechar_sesion()

    ui.label("Parcelas").classes("text-xl font-bold")
    rows = [
        {"id": p.id, "nome": p.nome, "superficie": p.superficie, "estado": p.estado}
        for p in parcelas
    ]
    ui.table(
        columns=[
            {"name": "nome", "label": "Nome", "field": "nome"},
            {"name": "superficie", "label": "Superficie", "field": "superficie"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows,
        row_key="id",
    )

    if pode_editar:
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
    ui.table(
        columns=[
            {"name": "especie", "label": "Especie", "field": "especie"},
            {"name": "raza", "label": "Raza", "field": "raza"},
            {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
            {"name": "estado", "label": "Estado", "field": "estado"},
        ],
        rows=rows_animais,
        row_key="id",
    )

    if pode_editar:
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

    if membro.rol == RolHorta.ADMIN:
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
