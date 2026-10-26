"""Diálogo «Nova tarefa»: un traballo por facer. Ábrese desde Tarefas e desde «Apuntar
traballo»."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.services.cultivos import listar_cultivos
from horta.services.parcelas import listar_parcelas
from horta.services.tarefas import crear_tarefa
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual

PRIORIDADES_TAREFA = ("baixa", "media", "alta")


def dialogo_nova_tarefa(horta_id: int) -> Callable[[], None]:
    """Constrúe o diálogo e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda: None
        opcions_parcela: dict[int | str, str] = {"": "(sen parcela)", **{
            p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}}
        opcions_cultivo: dict[int | str, str] = {"": "(sen cultivo)", **{
            c.id: c.especie for c in listar_cultivos(session, actor, horta_id)}}

    with ui.dialog() as dialogo, ui.card():
        ui.label("Nova tarefa").classes("text-md font-bold")
        descricion = ui.input("Que hai que facer").classes("w-full")
        parcela = ui.select(opcions_parcela, label="Parcela", value="").classes("w-full")
        cultivo = ui.select(opcions_cultivo, label="Cultivo", value="").classes("w-full")
        data = campo_data("Data (opcional)")
        prioridade = ui.select(list(PRIORIDADES_TAREFA), label="Prioridade", value="media")

        def crear() -> None:
            if not descricion.value:
                ui.notify("Escribe que hai que facer", type="negative")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                creada = executar_accion(session, lambda: crear_tarefa(
                    session, actor_actual, horta_id, descricion.value,
                    parcela_id=parcela.value or None, cultivo_id=cultivo.value or None,
                    data=parsear_data(data.value),
                    prioridade=prioridade.value))
            if creada:
                ui.navigate.reload()

        with ui.row():
            ui.button("Crear", icon="check", on_click=crear)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir() -> None:
        descricion.value = ""
        parcela.value = cultivo.value = ""
        data.value = ""
        prioridade.value = "media"
        dialogo.open()

    return abrir
