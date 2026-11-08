"""Sección Entradas e saídas de animais: nacementos, entradas, saídas e mortes de cada grupo
(libro de rexistro gandeiro). Baixa lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.movemento_animal import MovementoAnimal
from horta.models.tarefa import Tarefa
from horta.services.animais import listar_animais
from horta.services.diario import nome_grupo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.movementos_animais import (
    CON_OUTRA_EXPLOTACION,
    TIPOS_MOVEMENTO,
    DatosMovemento,
    actualizar_movemento,
    aviso_tempo_espera,
    crear_movemento,
    dar_de_baixa_movemento,
    listar_movementos,
)
from horta.services.persoas import listar_persoas, listar_quen
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campo_pago import CampoPago
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_movementos(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        movementos = listar_movementos(session, actor, horta_id)
        grupos = {a.id: nome_grupo(a.especie, a.raza)
                  for a in listar_animais(session, actor, horta_id)}
        persoas = {p.id: p.nome
                   for p in listar_persoas(session, actor, horta_id, so_activas=False)}

    filas = [{
        "id": mo.id,
        "data": f"{mo.data:%d/%m/%Y}",
        "grupo": grupos.get(mo.animal_id, ""),
        "tipo": TIPOS_MOVEMENTO[mo.tipo].split(" (")[0],
        "cantidade": mo.cantidade,
        "outra": persoas.get(mo.outra_parte_id or 0) or mo.causa or "",
        "quen": persoas.get(mo.persoa_id, "") if mo.persoa_id else "",
    } for mo in movementos]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("grupo", "Animais"), ("tipo", "Que"), ("cantidade", "Cantos"),
            ("outra", "Orixe, destino ou causa"), ("quen", "Quen"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai entradas nin saídas" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "data", ["tipo", "grupo", "cantidade"], accions_tarxeta)

    if not pode_editar:
        return
    abrir = dialogo_movemento(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        with get_session() as session:
            mo = session.get(MovementoAnimal, taboa.selected[0]["id"])
            if mo is not None:
                abrir(mo)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        movemento_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                mo = session.get(MovementoAnimal, movemento_id)
                if actor_actual is None or mo is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_movemento(
                    session, actor_actual, mo))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este rexistro? Non se borra: consérvase no histórico, e a "
            "cantidade do grupo recalcúlase.", confirmar)

    accions_tarxeta += [("Editar", "edit", editar),
                        ("Dar de baixa", "archive", dar_de_baixa)]

    with ui.row():
        ui.button("Apuntar entrada ou saída", icon="add", on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador"):
            ui.button("Editar", icon="edit", on_click=editar).props("outline")
            ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_movemento(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar unha entrada ou saída e devolve a función que
    o abre: abrir(movemento, tarefa=None, animal_id=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        animais = listar_animais(session, actor, horta_id)
        todos = {a.id: f"{nome_grupo(a.especie, a.raza)} · {a.cantidade}" for a in animais}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar entrada ou saída de animais").classes("text-h6")
        if not todos:
            ui.label("Primeiro engade os animais en Explotación → Animais.").classes(
                "text-warning text-caption")
        grupo = ui.select(todos, label="Animais", with_input=True).classes("w-full")
        tipo = ui.select(TIPOS_MOVEMENTO, label="Que pasou", value="saida").classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data("Data", date.today().isoformat()).classes(
                remove="w-full", add="col")
            cantidade = ui.input("Cantos animais").classes("col")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        aviso = ui.label("").classes("etiqueta-aviso")
        with ui.column().classes("w-full gap-0") as outra_explotacion:
            # Titular e REGA da outra explotación: ficha en Persoas
            outra_parte = CampoPersoa(horta_id, "explotacion", "Explotación de destino")
            codigo = ui.input("Nº de guía ou do movemento").classes("w-full")
            importe = ui.input("Prezo total (€)").classes("w-full")
            pago = CampoPago("Pagado ou cobrado")
        causa = ui.input("Causa").classes("w-full")
        identificacion = ui.input("Identificación dos animais (crotais, anelas…)").classes(
            "w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def mostrar_campos() -> None:
            outra_explotacion.set_visibility(tipo.value in CON_OUTRA_EXPLOTACION)
            outra_parte.set_label("Explotación de orixe (persoa titular anterior)"
                                  if tipo.value == "entrada"
                                  else "Explotación de destino (nova persoa titular)")
            causa.set_visibility(tipo.value == "morte")
            avisar()

        def avisar() -> None:
            texto = None
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is not None:
                    try:
                        dia = parsear_data(data.value)
                    except ValueError:
                        dia = None
                    texto = aviso_tempo_espera(session, actor_actual, horta_id, grupo.value,
                                               tipo.value, dia)
            aviso.text = texto or ""
            aviso.set_visibility(bool(texto))

        tipo.on_value_change(mostrar_campos)
        grupo.on_value_change(avisar)
        data.on_value_change(avisar)

        def gardar() -> None:
            if grupo.value is None or tipo.value is None:
                ui.notify("Escolle os animais e que pasou", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    cantos = parsear_decimal(cantidade.value)
                    datos = DatosMovemento(
                        animal_id=grupo.value, data=dia, tipo=tipo.value,
                        cantidade=int(cantos) if cantos is not None else 0,
                        persoa_id=persoa.value, identificacion=identificacion.value or None,
                        outra_parte_id=outra_parte.value,
                        codigo_movemento=codigo.value or None, causa=causa.value or None,
                        importe=parsear_decimal(importe.value), data_pago=pago.valor(dia),
                        horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None)
                    existente = (session.get(MovementoAnimal, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_movemento(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_movemento(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("movemento_animal", data.value)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(mo: MovementoAnimal | None, tarefa: Tarefa | None = None,
              animal_id: int | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = mo.id if mo else None
        titulo.text = ("Editar entrada ou saída de animais" if mo
                       else "Apuntar entrada ou saída de animais")
        animal_tarefa = tarefa.animal_id if tarefa and tarefa.animal_id in todos else None
        grupo.value = mo.animal_id if mo else (animal_id or animal_tarefa)
        tipo.value = mo.tipo if mo else "saida"
        data.value = (mo.data if mo else date.today()).isoformat()
        cantidade.value = str(mo.cantidade) if mo else ""
        persoa.value = (mo.persoa_id if mo.persoa_id in persoas else None) if mo else (
            proposta_quen(horta_id, tarefa))
        outra_parte.value = mo.outra_parte_id if mo else None
        codigo.value = (mo.codigo_movemento or "") if mo else ""
        causa.value = (mo.causa or "") if mo else ""
        importe.value = f"{mo.importe:g}" if mo and mo.importe is not None else ""
        pago.poñer(mo.data_pago if mo else None, mo is None)
        identificacion.value = (mo.identificacion or "") if mo else ""
        horas.value = f"{mo.horas:g}" if mo and mo.horas else ""
        maquina.value = mo.maquina_id if mo and mo.maquina_id in maquinas else None
        notas.value = (mo.notas or "") if mo else ""
        mostrar_campos()
        dialogo.open()

    return abrir
