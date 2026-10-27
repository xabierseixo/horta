"""Facer unha tarefa (un traballo por facer): con tipo, no formulario dese tipo xa enchido;
sen tipo, dicindo quen a fixo, cando e cantas horas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui
from sqlalchemy.orm import Session

from horta.db import Base, get_session
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.persoas import listar_persoas
from horta.services.tarefas import facer_tarefa, marcar_feita
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual


def rematar_tarefa(
    session: Session, actor: Usuario, tarefa_id: int | None, rexistro: Base
) -> None:
    """Despois de apuntar o traballo dunha tarefa, déixaa feita e ligada a el."""
    tarefa = session.get(Tarefa, tarefa_id) if tarefa_id else None
    if tarefa is not None:
        facer_tarefa(session, actor, tarefa, rexistro)


def dialogo_tarefa_feita(horta_id: int) -> Callable[[Tarefa], None]:
    """Diálogo para dar por feita unha tarefa sen tipo; devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    tarefa_id: dict[str, int | None] = {"id": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(28rem, 94vw)"):
        titulo = ui.label("").classes("text-h6")
        quen = ui.select(persoas, label="Quen o fixo").classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        horas = ui.input("Horas de traballo").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                tarefa = session.get(Tarefa, tarefa_id["id"])
                if tarefa is None:
                    ui.notify("Esa tarefa xa non existe", type="negative")
                    return
                ok = executar_accion(session, lambda: marcar_feita(
                    session, actor_actual, tarefa, quen.value, parsear_data(data.value),
                    parsear_decimal(horas.value)))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Feita", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(tarefa: Tarefa) -> None:
        tarefa_id["id"] = tarefa.id
        titulo.text = tarefa.descricion
        quen.value = proposta_quen(horta_id, tarefa)
        data.value = date.today().isoformat()
        horas.value = ""
        dialogo.open()

    return abrir
