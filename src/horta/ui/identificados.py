"""Animais identificados dun grupo (paso 14): opcional en todas as especies; no vacún,
ovino, caprino e équidos é obrigatorio identificar cada animal."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.animal import Animal, AnimalIdentificado
from horta.services.animais import (
    DISPOSITIVOS,
    SEXOS,
    actualizar_identificado,
    aviso_identificados,
    crear_identificado,
    listar_identificados,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.numeros import parsear_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _d(valor: date | None) -> str:
    return f"{valor:%d/%m/%Y}" if valor else ""


def abrir_identificados(horta_id: int, animal_id: int) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        animal = session.get(Animal, animal_id)
        if actor is None or animal is None:
            pechar_sesion()
            return
        individuos = listar_identificados(session, actor, animal)
        aviso = aviso_identificados(session, animal)
    por_id = {i.id: i for i in individuos}
    editando: dict[str, int | None] = {"id": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(44rem, 96vw)"):
        ui.label(f"Animais identificados: {animal.especie}").classes("text-h6")
        ui.label("Crotal, microchip ou anela de cada animal. Obrigatorio no vacún, ovellas, "
                 "cabras e cabalos (RD 787/2023); no porcino e nas aves a marca é da "
                 "explotación. Opcional no resto.").classes("texto-suave text-caption")
        if aviso:
            ui.label(aviso).classes("etiqueta-aviso")
        taboa = ui.table(
            columns=[{"name": k, "label": e, "field": k, "align": "left"} for k, e in (
                ("identificador", "Identificador"), ("nome", "Nome"), ("sexo", "Sexo"),
                ("alta", "Alta"), ("baixa", "Baixa"))],
            rows=[{"id": i.id, "identificador": i.identificador, "nome": i.nome or "",
                   "sexo": SEXOS.get(i.sexo or "", ""), "alta": _d(i.data_alta),
                   "baixa": _d(i.data_baixa)} for i in individuos],
            row_key="id", selection="single",
            on_select=lambda e: poñer(por_id.get(e.selection[0]["id"]) if e.selection
                                      else None),
        ).classes("w-full").props(f'flat bordered dense no-data-label="Ningún aínda" '
                                  f'{TEXTOS_TABOA}')
        ui.label("Novo ou editar o escollido").classes("text-subtitle2 q-mt-sm")
        with ui.row().classes("w-full no-wrap"):
            identificador = ui.input("Identificador").classes("col")
            nome = ui.input("Nome").classes("col")
            sexo = ui.select(SEXOS, label="Sexo", clearable=True).classes("w-32")
            dispositivo = ui.select(DISPOSITIVOS, label="Dispositivo", clearable=True).classes(
                "w-40")
        with ui.row().classes("w-full no-wrap"):
            nacemento = campo_data("Nacemento").classes(remove="w-full", add="col")
            alta = campo_data("Alta").classes(remove="w-full", add="col")
            baixa = campo_data("Baixa").classes(remove="w-full", add="col")

        def poñer(individuo: AnimalIdentificado | None) -> None:
            editando["id"] = individuo.id if individuo else None
            identificador.value = individuo.identificador if individuo else ""
            nome.value = (individuo.nome or "") if individuo else ""
            sexo.value = individuo.sexo if individuo else None
            dispositivo.value = individuo.dispositivo if individuo else None
            nacemento.value = (individuo.data_nacemento.isoformat()
                               if individuo and individuo.data_nacemento else "")
            alta.value = (individuo.data_alta if individuo else date.today()).isoformat()
            baixa.value = (individuo.data_baixa.isoformat()
                           if individuo and individuo.data_baixa else "")

        def gardar() -> None:
            campos = {"identificador": identificador.value or "", "nome": nome.value or None,
                      "sexo": sexo.value, "dispositivo": dispositivo.value,
                      "data_nacemento": parsear_data(nacemento.value),
                      "data_alta": parsear_data(alta.value),
                      "data_baixa": parsear_data(baixa.value)}
            with get_session() as session:
                actor_actual = usuario_actual(session)
                grupo = session.get(Animal, animal_id)
                if actor_actual is None or grupo is None:
                    return
                existente = (session.get(AnimalIdentificado, editando["id"])
                             if editando["id"] else None)
                ok = executar_accion(session, lambda: (
                    actualizar_identificado(session, actor_actual, existente, **campos)
                    if existente else crear_identificado(session, actor_actual, grupo,
                                                         **campos)))
            if ok:
                dialogo.close()
                abrir_identificados(horta_id, animal_id)

        def novo() -> None:
            taboa.selected.clear()
            taboa.update()
            poñer(None)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Novo", icon="add", on_click=novo).props("flat")
            ui.button("Pechar", on_click=dialogo.close).props("flat")
    poñer(None)
    dialogo.open()
