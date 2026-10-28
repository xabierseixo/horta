"""Tratamentos de postcolleita, almacén e transporte (caderno 3.3–3.5), baixo os tratamentos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.models.tratamento_instalacion import TIPOS_INSTALACION, TratamentoInstalacion
from horta.services.catalogos import describir, valores_vixentes
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_quen
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    actualizar_tratamento_instalacion,
    crear_tratamento_instalacion,
    dar_de_baixa_tratamento_instalacion,
    listar_tratamentos_instalacion,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_ETIQUETA_PROBLEMA = {"enfermidade": "Enfermidade", "praga": "Praga",
                      "mala_herba": "Mala herba", "regulador": "Regulador / outros"}
_QUE = {"postcolleita": "Produto vexetal tratado", "local": "Local (tipo e enderezo)",
        "transporte": "Vehículo (tipo, modelo e matrícula)"}
_CANTIDADE = {"postcolleita": "Cantidade de produto tratado (t)",
              "local": "Volume tratado (m³)", "transporte": "Volume tratado (m³)"}


def seccion_tratamentos_instalacion(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        tratamentos = listar_tratamentos_instalacion(session, actor, horta_id)
        filas = [{
            "id": t.id, "data": f"{t.data:%d/%m/%Y}", "tipo": TIPOS_INSTALACION[t.tipo],
            "que": t.obxecto,
            "problema": describir(session, t.problema_tipo, t.problema_codigo)
            if t.problema_tipo and t.problema_codigo else "",
            "produto": t.nome_comercial or t.materia_activa or "",
        } for t in tratamentos]

    ui.label("Postcolleita, almacéns e transporte").classes("text-h6 q-mt-lg")
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("tipo", "Tipo"), ("que", "Que se tratou"),
            ("problema", "Problema"), ("produto", "Produto"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Ningún tratamento destes" {TEXTOS_TABOA}')
    if not pode_editar:
        return

    abrir = dialogo_tratamento_instalacion(horta_id)

    def escollido() -> TratamentoInstalacion | None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un tratamento na táboa", type="warning")
            return None
        return next(t for t in tratamentos if t.id == taboa.selected[0]["id"])

    def editar() -> None:
        t = escollido()
        if t is not None:
            abrir(t)

    def dar_de_baixa() -> None:
        t = escollido()
        if t is None:
            return
        tratamento_id = t.id

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                x = session.get(TratamentoInstalacion, tratamento_id)
                if actor_actual is None or x is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_tratamento_instalacion(
                    session, actor_actual, x))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este tratamento? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar postcolleita, almacén ou transporte", icon="add",
                  on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_tratamento_instalacion(
    horta_id: int,
) -> Callable[[TratamentoInstalacion | None], None]:
    """Constrúe o diálogo do tratamento de instalacións e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        problemas = {t: {v.codigo: v.descricion for v in valores_vixentes(session, t)}
                     for t in TIPOS_PROBLEMA}
        xustificacions = {v.codigo: v.descricion
                          for v in valores_vixentes(session, "xustificacion")}
        tipos_produto = {v.codigo: v.descricion
                         for v in valores_vixentes(session, "tipo_produto")}
        unidades = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar tratamento").classes("text-h6")
        tipo = ui.select(TIPOS_INSTALACION, value="postcolleita", label="Que tipo").classes(
            "w-full")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        obxecto = ui.input(_QUE["postcolleita"]).classes("w-full")
        catastro = ui.input("Referencia catastral do local").classes("w-full")
        catastro.bind_visibility_from(tipo, "value", backward=lambda v: v == "local")
        cantidade_tratada = ui.input(_CANTIDADE["postcolleita"]).classes("w-full")

        def cambiar_tipo() -> None:
            obxecto.props(f'label="{_QUE[tipo.value]}"')
            cantidade_tratada.props(f'label="{_CANTIDADE[tipo.value]}"')

        tipo.on_value_change(cambiar_tipo)
        tipo_problema = ui.select(_ETIQUETA_PROBLEMA, value="praga",
                                  label="Tipo de problema").classes("w-full")
        problema = ui.select(problemas["praga"], label="Problema", with_input=True,
                             clearable=True).classes("w-full")
        tipo_problema.on_value_change(
            lambda e: problema.set_options(problemas[e.value], value=None))
        xustificacion = ui.select(xustificacions, label="Xustificación",
                                  clearable=True).classes("w-full")
        tipo_produto = ui.select(tipos_produto, label="Tipo de produto",
                                 clearable=True).classes("w-full")
        nome_comercial = ui.input("Nome comercial").classes("w-full")
        num_rexistro = ui.input("Nº de rexistro").classes("w-full")
        materia_activa = ui.input("Materia activa").classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            cantidade = ui.input("Cantidade utilizada").classes("col")
            unidade = ui.select(unidades, label="Unidade", with_input=True).classes("col")
        horas = ui.input("Horas de traballo").classes("w-full")
        maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
        notas = ui.textarea("Notas").classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosTratamentoInstalacion(
                        tipo=tipo.value, data=dia, obxecto=obxecto.value or "",
                        referencia_catastral=catastro.value if tipo.value == "local" else None,
                        problema_tipo=tipo_problema.value if problema.value else None,
                        problema_codigo=problema.value, xustificacion=xustificacion.value,
                        cantidade_tratada=parsear_decimal(cantidade_tratada.value),
                        tipo_produto=tipo_produto.value,
                        nome_comercial=nome_comercial.value or None,
                        num_rexistro=num_rexistro.value or None,
                        materia_activa=materia_activa.value or None,
                        cantidade_utilizada=parsear_decimal(cantidade.value),
                        unidade=unidade.value, notas=notas.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value)
                    existente = (session.get(TratamentoInstalacion, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_tratamento_instalacion(session, actor_actual, horta_id, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_tratamento_instalacion(session, actor_actual, existente,
                                                          datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(t: TratamentoInstalacion | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = t.id if t else None
        titulo.text = "Editar tratamento" if t else "Apuntar tratamento"
        tipo.value = t.tipo if t else "postcolleita"
        data.value = (t.data if t else date.today()).isoformat()
        persoa.value = (t.persoa_id if t.persoa_id in persoas else None) if t else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{t.horas:g}" if t and t.horas else ""
        maquina.value = t.maquina_id if t and t.maquina_id in maquinas else None
        obxecto.value = t.obxecto if t else ""
        catastro.value = (t.referencia_catastral or "") if t else ""
        cantidade_tratada.value = f"{t.cantidade_tratada:g}" if t and t.cantidade_tratada \
            else ""
        tipo_problema.value = (t.problema_tipo or "praga") if t else "praga"
        problema.value = t.problema_codigo if t else None
        xustificacion.value = t.xustificacion if t else None
        tipo_produto.value = t.tipo_produto if t else None
        nome_comercial.value = (t.nome_comercial or "") if t else ""
        num_rexistro.value = (t.num_rexistro or "") if t else ""
        materia_activa.value = (t.materia_activa or "") if t else ""
        cantidade.value = f"{t.cantidade_utilizada:g}" if t and t.cantidade_utilizada else ""
        unidade.value = t.unidade if t else None
        notas.value = (t.notas or "") if t else ""
        cambiar_tipo()
        dialogo.open()

    return abrir
