"""Formulario de «Outro traballo» (mantemento, limpeza, arranxos…). Non ten táboa propia: a
súa lista é o Diario."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.outro_traballo import OutroTraballo
from horta.models.tarefa import Tarefa
from horta.services.animais import listar_animais
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.outros_traballos import (
    DatosOutroTraballo,
    actualizar_outro_traballo,
    crear_outro_traballo,
    dar_de_baixa_outro_traballo,
)
from horta.services.parcelas import listar_parcelas
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual


def dialogo_outro_traballo(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar outro traballo e devolve a función que o abre:
    abrir(traballo, tarefa=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        parcelas = {p.id: p.nome for p in listar_parcelas(session, actor, horta_id)}
        animais = {a.id: nome_grupo(a.especie, a.raza)
                   for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Apuntar outro traballo").classes("text-h6")
        descricion = ui.input("Que se fixo (p.ex. arranxar o peche)").classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        data_fin = campo_data("Data de fin (se durou máis dun día)")
        parcela = ui.select(parcelas, label="Parcela (se foi nunha)", clearable=True).classes(
            "w-full")
        animal = ui.select(animais, label="Animais (se foi con eles)", clearable=True).classes(
            "w-full")
        ui.label("Sen parcela nin animais, é un traballo da explotación enteira.").classes(
            "text-caption texto-suave")
        with ui.row().classes("w-full no-wrap"):
            persoa = ui.select(persoas, label="Quen o fixo").classes("col")
            horas = ui.input("Horas").classes("col")
        with ui.expansion("Máis datos").classes("w-full"):
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data_inicio.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosOutroTraballo(
                        horta_id=horta_id, data_inicio=dia,
                        data_fin=parsear_data(data_fin.value),
                        descricion=descricion.value or "", parcela_id=parcela.value,
                        animal_id=animal.value, persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                        notas=notas.value or None)
                    existente = (session.get(OutroTraballo, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_outro_traballo(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_outro_traballo(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        def dar_de_baixa() -> None:
            def confirmar() -> None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is None:
                        pechar_sesion()
                        return
                    traballo = session.get(OutroTraballo, editando["id"])
                    if traballo is None:
                        return
                    ok = executar_accion(session, lambda: dar_de_baixa_outro_traballo(
                        session, actor_actual, traballo))
                if ok:
                    ui.navigate.reload()

            confirmar_eliminacion(
                "Dar de baixa este traballo? Non se borra: consérvase no histórico.", confirmar)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            baixa = ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props(
                "flat")
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(traballo: OutroTraballo | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = traballo.id if traballo else None
        titulo.text = "Editar outro traballo" if traballo else "Apuntar outro traballo"
        descricion.value = (traballo.descricion if traballo
                            else tarefa.descricion if tarefa else "")
        data_inicio.value = (traballo.data_inicio if traballo else date.today()).isoformat()
        data_fin.value = (traballo.data_fin.isoformat()
                          if traballo and traballo.data_fin != traballo.data_inicio else "")
        if traballo:
            parcela.value = traballo.parcela_id if traballo.parcela_id in parcelas else None
            animal.value = traballo.animal_id if traballo.animal_id in animais else None
        else:
            parcela.value = tarefa.parcela_id if tarefa and tarefa.parcela_id in parcelas \
                else None
            animal.value = tarefa.animal_id if tarefa and tarefa.animal_id in animais else None
        persoa.value = ((traballo.persoa_id if traballo.persoa_id in persoas else None)
                        if traballo else proposta_quen(horta_id, tarefa))
        horas.value = f"{traballo.horas:g}" if traballo and traballo.horas else ""
        maquina.value = (traballo.maquina_id if traballo and traballo.maquina_id in maquinas
                         else None)
        notas.value = (traballo.notas or "") if traballo else ""
        baixa.set_visibility(traballo is not None)
        dialogo.open()

    return abrir
