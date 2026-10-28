"""Sección Produción dos animais: ovos, leite, mel... de cada grupo, co seu lote. Baixa
lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.producion_animal import ProducionAnimal
from horta.models.tarefa import Tarefa
from horta.services.animais import listar_animais
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.services.producions_animais import (
    PRODUTOS,
    UNIDADE_PRODUTO,
    UNIDADES_PRODUCION,
    DatosProducion,
    actualizar_producion,
    aviso_tempo_espera,
    crear_producion,
    dar_de_baixa_producion,
    listar_producions,
    produtos_da_especie,
    propor_lote,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_producion(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        producions = listar_producions(session, actor, horta_id)
        grupos = {a.id: nome_grupo(a.especie, a.raza)
                  for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

    filas = [{
        "id": pr.id,
        "data": (f"{pr.data:%d/%m/%Y}" if pr.data_fin == pr.data
                 else f"{pr.data:%d/%m} – {pr.data_fin:%d/%m/%Y}"),
        "grupo": grupos.get(pr.animal_id, ""),
        "produto": PRODUTOS[pr.produto],
        "cantidade": f"{pr.cantidade:g} {pr.unidade}",
        "retirada": f"{pr.retirada:g}" if pr.retirada else "",
        "lote": pr.lote,
        "quen": persoas.get(pr.persoa_id, "") if pr.persoa_id else "",
    } for pr in producions]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("grupo", "Animais"), ("produto", "Produto"),
            ("cantidade", "Canto"), ("retirada", "Retirado"), ("lote", "Lote"),
            ("quen", "Quen"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai produción apuntada" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_producion(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        with get_session() as session:
            pr = session.get(ProducionAnimal, taboa.selected[0]["id"])
            if pr is not None:
                abrir(pr)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        producion_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                pr = session.get(ProducionAnimal, producion_id)
                if actor_actual is None or pr is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_producion(
                    session, actor_actual, pr))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este rexistro? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar produción", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_producion(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar a produción e devolve a función que o abre:
    abrir(producion, tarefa=None, animal_id=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        animais = listar_animais(session, actor, horta_id)
        todos = {a.id: nome_grupo(a.especie, a.raza) for a in animais}
        especies = {a.id: a.especie_codigo for a in animais}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar produción dos animais").classes("text-h6")
        if not todos:
            ui.label("Primeiro engade os animais en Explotación → Animais.").classes(
                "text-warning text-caption")
        grupo = ui.select(todos, label="Animais", with_input=True).classes("w-full")
        produto = ui.select(PRODUTOS, label="Produto").classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data("Data", date.today().isoformat()).classes(
                remove="w-full", add="col")
            data_fin = campo_data("Ata (opcional)", "").classes(
                remove="w-full", add="col")
        with ui.row().classes("w-full no-wrap"):
            cantidade = ui.input("Canto").classes("col")
            unidade = ui.select(list(UNIDADES_PRODUCION), label="Unidade",
                                value="unidades").classes("col")
        retirada = ui.input("Retirado: rotos ou que non vale").classes("w-full")
        aviso = ui.label("").classes("etiqueta-aviso")
        todo_retirado = ui.button("Poñer todo como retirado", icon="block",
                                  on_click=lambda: retirada.set_value(cantidade.value)).props(
            "flat dense")
        lote = ui.input("Lote").classes("w-full")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def dias() -> tuple[date | None, date | None]:
            try:
                return parsear_data(data.value), parsear_data(data_fin.value)
            except ValueError:
                return None, None

        def avisar() -> None:
            texto = None
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is not None:
                    inicio, fin = dias()
                    texto = aviso_tempo_espera(session, actor_actual, horta_id, grupo.value,
                                               inicio, fin)
            aviso.text = texto or ""
            aviso.set_visibility(bool(texto))
            todo_retirado.set_visibility(bool(texto))

        def propor() -> None:
            if editando["id"] is not None or produto.value is None:
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is not None:
                    lote.value = propor_lote(session, actor_actual, horta_id, produto.value,
                                             dias()[0] or date.today())

        def produtos_do_grupo() -> None:
            opcions = produtos_da_especie(especies.get(grupo.value)) if grupo.value else PRODUTOS
            produto.set_options(opcions, value=produto.value if produto.value in opcions
                                else next(iter(opcions)))
            avisar()

        def cambiar_produto() -> None:
            if editando["id"] is None and produto.value is not None:
                unidade.value = UNIDADE_PRODUTO[produto.value]
            propor()

        grupo.on_value_change(produtos_do_grupo)
        produto.on_value_change(cambiar_produto)
        data.on_value_change(avisar)
        data_fin.on_value_change(avisar)

        def gardar() -> None:
            if grupo.value is None or produto.value is None:
                ui.notify("Escolle os animais e o produto", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    inicio = parsear_data(data.value)
                    if inicio is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    canto = parsear_decimal(cantidade.value)
                    datos = DatosProducion(
                        animal_id=grupo.value, data=inicio, data_fin=parsear_data(data_fin.value),
                        produto=produto.value, cantidade=canto if canto is not None else 0,
                        unidade=unidade.value, retirada=parsear_decimal(retirada.value),
                        lote=lote.value or "", persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None)
                    existente = (session.get(ProducionAnimal, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_producion(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_producion(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(pr: ProducionAnimal | None, tarefa: Tarefa | None = None,
              animal_id: int | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = pr.id if pr else None
        titulo.text = ("Editar produción dos animais" if pr
                       else "Apuntar produción dos animais")
        animal_tarefa = tarefa.animal_id if tarefa and tarefa.animal_id in todos else None
        grupo.value = pr.animal_id if pr else (animal_id or animal_tarefa)
        produtos_do_grupo()
        if pr:
            produto.value = pr.produto
        data.value = (pr.data if pr else date.today()).isoformat()
        data_fin.value = (pr.data_fin.isoformat() if pr and pr.data_fin != pr.data else "")
        cantidade.value = f"{pr.cantidade:g}" if pr else ""
        unidade.value = pr.unidade if pr else UNIDADE_PRODUTO[produto.value or "outro"]
        retirada.value = f"{pr.retirada:g}" if pr and pr.retirada else ""
        lote.value = pr.lote if pr else ""
        propor()
        persoa.value = (pr.persoa_id if pr.persoa_id in persoas else None) if pr else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{pr.horas:g}" if pr and pr.horas else ""
        maquina.value = pr.maquina_id if pr and pr.maquina_id in maquinas else None
        notas.value = (pr.notas or "") if pr else ""
        avisar()
        dialogo.open()

    return abrir
