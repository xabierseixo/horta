from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela
from horta.models.tratamento_fito import TIPOS_PROBLEMA, TratamentoFito
from horta.services.catalogos import describir, valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.services.tratamentos_fito import (
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
    dar_de_baixa_tratamento_fito,
    faltas_para_cue,
    listar_tratamentos_fito,
)
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal, parsear_hora
from horta.ui.sesion import pechar_sesion, usuario_actual

_ETIQUETA_PROBLEMA = {"enfermidade": "Enfermidade", "praga": "Praga (artrópodos/gasterópodos)",
                      "mala_herba": "Mala herba", "regulador": "Regulador / outros"}


def _obrigatoria(valor: date | None) -> date:
    if valor is None:
        raise OperacionNonPermitidaError("Indica as datas de inicio e fin")
    return valor


def _opcions(session, catalogo: str) -> dict[str, str]:
    return {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}


def seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        tratamentos = listar_tratamentos_fito(session, actor, horta_id)
        filas = []
        for t in tratamentos:
            cultivos = [session.get(Cultivo, c.cultivo_id) for c in t.cultivos]
            filas.append({
                "id": t.id,
                "data": f"{t.data_inicio:%d/%m/%Y}",
                "cultivos": ", ".join(c.especie for c in cultivos if c),
                "problemas": ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
                or (t.observacions or ""),
                "produtos": ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
                or (t.orixinal_produto or ""),
                "cue": "completo" if not faltas_para_cue(t)
                else "falta: " + ", ".join(faltas_para_cue(t)),
            })
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        opcions_cultivo = {c.id: f"{c.especie} {c.variedade or ''} — "
                                 f"{parcelas[c.parcela_id].nome}".strip()
                           for c in cultivos_horta}
        problemas = {tipo: _opcions(session, tipo) for tipo in TIPOS_PROBLEMA}
        xustificacions = _opcions(session, "xustificacion")
        estados = _opcions(session, "estado_fenoloxico")
        unidades = _opcions(session, "unidade_medida")
        tipos_produto = _opcions(session, "tipo_produto")
        eficacias = _opcions(session, "eficacia")
        aplicadores = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)
                       if p.e_aplicador}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivos", "Cultivos"), ("problemas", "Problema"),
            ("produtos", "Produtos"), ("cue", "CUE"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full").props('no-data-label="Aínda non hai tratamentos rexistrados"')

    if not pode_editar:
        return
    if not problemas["enfermidade"]:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return

    with ui.dialog() as dialogo, ui.card().style("min-width: 40rem"):
        with ui.stepper().props("vertical").classes("w-full") as pasos:
            with ui.step("1. Que e onde"):
                data_inicio = ui.input("Data de inicio (AAAA-MM-DD)",
                                       value=date.today().isoformat()).classes("w-full")
                data_fin = ui.input(
                    "Data de fin (AAAA-MM-DD)", value=date.today().isoformat()
                ).classes("w-full")
                hora = ui.input("Hora de inicio (HH:MM, opcional)").classes("w-full")
                cultivo = ui.select(opcions_cultivo, label="Cultivo e parcela",
                                    with_input=True).classes("w-full")
                superficie = ui.input("Superficie tratada (ha)").classes("w-full")
                estado = ui.select(estados, label="Estado fenolóxico").classes("w-full")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
            with ui.step("2. Por que"):
                tipo_problema = ui.select(_ETIQUETA_PROBLEMA, value="enfermidade",
                                          label="Tipo de problema").classes("w-full")
                problema = ui.select(problemas["enfermidade"], label="Problema",
                                     with_input=True).classes("w-full")
                tipo_problema.on_value_change(
                    lambda e: problema.set_options(problemas[e.value], value=None))
                xustificacion = ui.select(xustificacions, label="Xustificación").classes("w-full")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("3. Con que"):
                tipo_produto = ui.select(tipos_produto, value=next(iter(tipos_produto), None),
                                         label="Tipo de produto")
                nome_comercial = ui.input("Nome comercial").classes("w-full")
                num_rexistro = ui.input("Nº de rexistro").classes("w-full")
                materia_activa = ui.input("Materia activa").classes("w-full")
                dose = ui.input("Dose (por hectárea)").classes("w-full")
                unidade = ui.select(unidades, label="Unidade", with_input=True).classes("w-full")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("4. Quen"):
                aplicador = ui.select(aplicadores, label="Aplicador").classes("w-full")
                maquina = ui.select(
                    maquinas, label="Máquina (baleiro se é manual)"
                ).classes("w-full")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("5. Resultado"):
                eficacia = ui.select(eficacias, label="Eficacia").classes("w-full")
                observacions = ui.textarea("Observacións").classes("w-full")

                def gardar() -> None:
                    if cultivo.value is None or problema.value is None:
                        ui.notify("Indica o cultivo e o problema", type="negative")
                        return
                    with get_session() as session:
                        actor_actual = usuario_actual(session)
                        if actor_actual is None:
                            pechar_sesion()
                            return

                        def crear() -> None:
                            datos = DatosTratamento(
                                data_inicio=_obrigatoria(parsear_data(data_inicio.value)),
                                data_fin=_obrigatoria(parsear_data(data_fin.value)),
                                hora=parsear_hora(hora.value),
                                cultivos=[LinhaCultivo(cultivo.value,
                                                       parsear_decimal(superficie.value),
                                                       estado.value)],
                                problemas=[Problema(tipo_problema.value, problema.value)],
                                xustificacions=[xustificacion.value] if xustificacion.value
                                else [],
                                produtos=[LinhaProduto(
                                    tipo_produto=tipo_produto.value, unidade=unidade.value,
                                    num_rexistro=num_rexistro.value or None,
                                    nome_comercial=nome_comercial.value or None,
                                    materia_activa=materia_activa.value or None,
                                    dose=parsear_decimal(dose.value))],
                                aplicadores=[LinhaAplicador(aplicador.value, maquina.value,
                                                            aplicacion_manual=maquina.value
                                                            is None)]
                                if aplicador.value else [],
                                eficacia=eficacia.value,
                                observacions=observacions.value or None,
                            )
                            crear_tratamento_fito(session, actor_actual, horta_id, datos)

                        ok = executar_accion(session, crear)
                    if ok:
                        ui.navigate.reload()

                with ui.stepper_navigation():
                    ui.button("Gardar", icon="check", on_click=gardar)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
        ui.button("Pechar", on_click=dialogo.close).props("flat")

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Selecciona un tratamento na táboa", type="warning")
            return
        tratamento_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                tratamento = session.get(TratamentoFito, tratamento_id)
                if actor_actual is None or tratamento is None:
                    return
                ok = executar_accion(
                    session,
                    lambda: dar_de_baixa_tratamento_fito(session, actor_actual, tratamento),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este tratamento? Non se borra: consérvase no histórico "
            "(obriga legal), pero deixa de aparecer na lista.",
            confirmar,
        )

    with ui.row():
        ui.button("Novo tratamento", icon="add", on_click=dialogo.open)
        ui.button("Dar de baixa o seleccionado", icon="archive", on_click=dar_de_baixa).props(
            "outline"
        )
