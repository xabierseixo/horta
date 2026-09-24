from __future__ import annotations

from datetime import date

from nicegui import app, ui
from sqlalchemy.orm import Session

from horta.db import get_session
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.animais import crear_animal, listar_animais
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import comprobar_rol_horta
from horta.services.parcelas import crear_parcela, listar_parcelas

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def _actor(session: Session) -> Usuario:
    usuario = session.get(Usuario, app.storage.user["usuario_id"])
    assert usuario is not None
    return usuario


@ui.page("/hortas/{horta_id}")
def horta_detalle_page(horta_id: int) -> None:
    with get_session() as session:
        actor = _actor(session)
        try:
            membro = comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
        except PermisoDenegadoError:
            ui.label("Non tes acceso a esta horta").classes("text-negative")
            return
        parcelas = listar_parcelas(session, actor, horta_id)
        animais = listar_animais(session, actor, horta_id)
        pode_editar = membro.rol in _ROLES_ESCRITURA

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
                    actor_actual = _actor(session)
                    crear_parcela(
                        session,
                        actor_actual,
                        horta_id,
                        nome_input.value,
                        superficie=superficie_input.value,
                    )
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
                    actor_actual = _actor(session)
                    crear_animal(
                        session,
                        actor_actual,
                        horta_id,
                        especie_input.value,
                        date.today(),
                        raza=raza_input.value or None,
                        cantidade=int(cantidade_input.value or 1),
                    )
                ui.navigate.reload()

            ui.button("Crear animal", on_click=crear_animal_novo)
