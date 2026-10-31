"""Diálogo do tratamento fitosanitario, con varias filas de cultivos, problemas, produtos e
medidas, o asesor e os avisos do rexistro do MAPA (deseño 2026-10-25-tratamentos-completos)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_consulta import AVISO, FORTE, comprobar_tratamento, materia_activa
from horta.services.tratamentos_fito import (
    UNIDADES_DOSE,
    UNIDADES_TOTAL,
    DatosAsesor,
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaMedida,
    LinhaProduto,
    Problema,
    actualizar_tratamento_fito,
    crear_tratamento_fito,
)
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal, parsear_hora
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.tempo import EtiquetaTempo

ETIQUETA_PROBLEMA = {"enfermidade": "Enfermidade", "praga": "Praga (artrópodos/gasterópodos)",
                     "mala_herba": "Mala herba", "regulador": "Regulador / outros"}
_PASO_RESULTADO = "5. Resultado"
_REXISTRADO = "1"


@dataclass
class OpcionsTratamento:
    cultivos: dict[int, str]
    problemas: dict[str, dict[str, str]]
    xustificacions: dict[str, str]
    estados: dict[str, str]
    unidades: dict[str, str]
    tipos_produto: dict[str, str]
    tipos_medida: dict[str, str]
    eficacias: dict[str, str]
    aplicadores: dict[int, str]
    asesores: dict[int, str]
    maquinas: dict[int, str]
    rexistro: dict[str, str]
    superficies: dict[int, float] = field(default_factory=dict)  # do cultivo, en ha


def _txt(valor: float | None) -> str:
    return f"{valor:g}" if valor is not None else ""


def _ou_nada(opcions: dict[Any, str], valor: Any) -> Any:
    return valor if valor in opcions else None


def _papeleira(lista: list[dict[str, Any]], fila: dict[str, Any],
               refrescar: Callable[[], Any]) -> None:
    def quitar() -> None:
        lista.remove(fila)
        refrescar()

    ui.button(icon="delete", on_click=quitar).props("flat dense round").tooltip("Quitar")


def crear_dialogo_tratamento(
    horta_id: int, op: OpcionsTratamento
) -> Callable[[TratamentoFito | None], None]:
    """Constrúe o diálogo e devolve a función que o abre (None = tratamento novo)."""
    estado: dict[str, Any] = {"id": None, "cultivos": [], "problemas": [], "produtos": [],
                              "medidas": [], "orixinais": "", "tarefa": None}

    def fila_cultivo(cultivo_id: int | None = None, superficie: str = "",
                     fenoloxico: str | None = None) -> dict[str, Any]:
        if not superficie and cultivo_id in op.superficies:
            superficie = _txt(op.superficies[cultivo_id])
        return {"cultivo_id": _ou_nada(op.cultivos, cultivo_id), "superficie": superficie,
                "estado": _ou_nada(op.estados, fenoloxico)}

    def fila_problema(tipo: str = "enfermidade", codigo: str | None = None) -> dict[str, Any]:
        return {"tipo": tipo, "codigo": _ou_nada(op.problemas[tipo], codigo)}

    def fila_produto(**valores: Any) -> dict[str, Any]:
        fila = {"rexistro": None, "tipo_produto": _REXISTRADO, "nome": "", "num": "",
                "materia": "", "dose": "", "unidade": None, "total": False}
        fila.update(valores)
        fila["tipo_produto"] = _ou_nada(op.tipos_produto, fila["tipo_produto"])
        fila["unidade"] = _ou_nada(op.unidades, fila["unidade"])
        fila["rexistro"] = _ou_nada(op.rexistro, fila["num"])
        return fila

    def fila_medida(tipo: str | None = None, cantidade: str = "", unidade: str | None = None,
                    mdf: str = "") -> dict[str, Any]:
        return {"tipo": _ou_nada(op.tipos_medida, tipo), "cantidade": cantidade,
                "unidade": _ou_nada(op.unidades, unidade), "mdf": mdf}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(46rem, 96vw)"):
        with ui.stepper().props("vertical").classes("w-full") as pasos:
            with ui.step("1. Que e onde"):
                with ui.row().classes("w-full"):
                    data_inicio = campo_data("Data de inicio").classes("grow")
                    data_fin = campo_data("Data de fin").classes("grow")
                hora = ui.input("Hora de inicio (HH:MM, opcional)").classes("w-full")
                tempo = EtiquetaTempo(horta_id, "tratamento")

                def mirar_tempo() -> None:
                    cultivos = [f["cultivo_id"] for f in estado["cultivos"] if f["cultivo_id"]]
                    tempo.actualizar(data_inicio.value, cultivos)

                data_inicio.on_value_change(mirar_tempo)

                def seguir_inicio() -> None:
                    # A fin segue ao inicio mentres non se cambiou a man
                    fin, inicio = data_fin.value, data_inicio.value
                    if not fin or fin == estado["inicio"] or (inicio and fin < inicio):
                        data_fin.value = inicio
                    estado["inicio"] = inicio

                data_inicio.on_value_change(seguir_inicio)
                ui.label("Cultivos tratados (mesmo cultivo e variedade)").classes("text-bold")

                @ui.refreshable
                def filas_cultivos() -> None:
                    for fila in estado["cultivos"]:
                        with ui.row().classes("w-full items-end gap-2"):
                            def escoller_cultivo(e: Any, f: dict[str, Any] = fila) -> None:
                                if not f["superficie"] and e.value in op.superficies:
                                    f["superficie"] = _txt(op.superficies[e.value])
                                mirar_tempo()

                            ui.select(op.cultivos, label="Cultivo e parcela",
                                      with_input=True, on_change=escoller_cultivo).bind_value(
                                fila, "cultivo_id").classes("grow")
                            ui.input("Superficie (ha)").bind_value(fila, "superficie").classes(
                                "w-28")
                            ui.select(op.estados, label="Estado fenolóxico").bind_value(
                                fila, "estado").classes("w-40")
                            _papeleira(estado["cultivos"], fila, filas_cultivos.refresh)

                    def engadir() -> None:
                        estado["cultivos"].append(fila_cultivo())
                        filas_cultivos.refresh()

                    ui.button("Engadir cultivo", icon="add", on_click=engadir).props("flat dense")

                filas_cultivos()

                @ui.refreshable
                def orixinais() -> None:
                    if estado["orixinais"]:
                        ui.label(f"Datos orixinais (antes da migración): {estado['orixinais']}"
                                 ).classes("text-sm text-grey-8")

                orixinais()
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
            with ui.step("2. Por que"):

                @ui.refreshable
                def filas_problemas() -> None:
                    for fila in estado["problemas"]:
                        with ui.row().classes("w-full items-end gap-2"):

                            def cambiar_tipo(e: Any, f: dict[str, Any] = fila) -> None:
                                f["tipo"], f["codigo"] = e.value, None
                                filas_problemas.refresh()

                            ui.select(ETIQUETA_PROBLEMA, value=fila["tipo"], label="Tipo",
                                      on_change=cambiar_tipo).classes("w-48")
                            ui.select(op.problemas[fila["tipo"]], label="Problema",
                                      with_input=True).bind_value(fila, "codigo").classes("grow")
                            _papeleira(estado["problemas"], fila, filas_problemas.refresh)

                    def engadir() -> None:
                        estado["problemas"].append(fila_problema())
                        filas_problemas.refresh()

                    ui.button("Engadir problema", icon="add", on_click=engadir).props(
                        "flat dense")

                filas_problemas()
                xustificacions = ui.select(op.xustificacions, label="Xustificacións",
                                           multiple=True).classes("w-full").props("use-chips")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("3. Con que"):

                @ui.refreshable
                def filas_produtos() -> None:
                    for fila in estado["produtos"]:
                        with ui.card().classes("w-full q-pa-sm"):
                            with ui.row().classes("w-full items-end gap-2"):

                                def escoller(e: Any, f: dict[str, Any] = fila) -> None:
                                    # Os campos ligados á fila actualízanse sós: sen refresh,
                                    # que volvería disparar este evento
                                    if not e.value or e.value == f["num"]:
                                        return
                                    with get_session() as session:
                                        f["materia"] = materia_activa(session, e.value)
                                    f["num"], f["tipo_produto"] = e.value, _REXISTRADO
                                    f["nome"] = op.rexistro[e.value].rsplit(" (", 1)[0]

                                ui.select(op.rexistro, label="Buscar no rexistro do MAPA "
                                          "(nome ou nº)", with_input=True, clearable=True,
                                          on_change=escoller).bind_value(
                                    fila, "rexistro").classes("grow")
                                _papeleira(estado["produtos"], fila, filas_produtos.refresh)
                            with ui.row().classes("w-full items-end gap-2"):
                                ui.select(op.tipos_produto, label="Tipo de produto").bind_value(
                                    fila, "tipo_produto").classes("w-56")
                                ui.input("Nome comercial").bind_value(fila, "nome").classes(
                                    "grow")
                                ui.input("Nº de rexistro").bind_value(fila, "num").classes(
                                    "w-32")
                            ui.input("Materia activa").bind_value(fila, "materia").classes(
                                "w-full")
                            with ui.row().classes("w-full items-end gap-2"):
                                ui.input("Dose").bind_value(fila, "dose").classes("w-28")
                                ui.select({k: v for k, v in op.unidades.items()
                                           if k in UNIDADES_DOSE + UNIDADES_TOTAL},
                                          label="Unidade").bind_value(fila, "unidade").classes(
                                    "grow")
                            ui.checkbox("É a cantidade total, non a dose por hectárea"
                                        ).bind_value(fila, "total")

                    def engadir() -> None:
                        estado["produtos"].append(fila_produto())
                        filas_produtos.refresh()

                    ui.button("Engadir produto", icon="add", on_click=engadir).props(
                        "flat dense")

                filas_produtos()
                ui.label("Medidas non químicas (trampas, confusión sexual, fauna útil…)"
                         ).classes("text-bold")

                @ui.refreshable
                def filas_medidas() -> None:
                    for fila in estado["medidas"]:
                        with ui.row().classes("w-full items-end gap-2"):
                            ui.select(op.tipos_medida, label="Medida").bind_value(
                                fila, "tipo").classes("grow")
                            ui.input("Cantidade").bind_value(fila, "cantidade").classes("w-24")
                            ui.select(op.unidades, label="Unidade",
                                      with_input=True).bind_value(fila, "unidade").classes(
                                "w-36")
                            ui.input("Nº rexistro MDF").bind_value(fila, "mdf").classes("w-32")
                            _papeleira(estado["medidas"], fila, filas_medidas.refresh)

                    def engadir() -> None:
                        estado["medidas"].append(fila_medida())
                        filas_medidas.refresh()

                    ui.button("Engadir medida", icon="add", on_click=engadir).props("flat dense")

                filas_medidas()
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("4. Quen"):
                aplicador = ui.select(op.aplicadores, label="Aplicador").classes("w-full")
                maquina = ui.select(op.maquinas, label="Máquina (baleiro se é manual)"
                                    ).classes("w-full")
                asesor = ui.select(op.asesores, label="Asesor (opcional)",
                                   clearable=True).classes("w-full")
                data_asesor = campo_data("Data do asesoramento")
                validacion = ui.checkbox("O asesor validou o tratamento")
                for campo in (asesor, data_asesor, validacion):
                    campo.set_visibility(bool(op.asesores))
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step(_PASO_RESULTADO):
                eficacia = ui.select(op.eficacias, label="Eficacia").classes("w-full")
                notas = ui.textarea("Notas").classes("w-full")
                ui.label("Comprobación co rexistro do MAPA (a etiqueta é a referencia legal)"
                         ).classes("text-bold")

                def datos() -> DatosTratamento:
                    inicio = parsear_data(data_inicio.value)
                    fin = parsear_data(data_fin.value)
                    if inicio is None or fin is None:
                        raise OperacionNonPermitidaError("Indica as datas de inicio e fin")
                    data_as = parsear_data(data_asesor.value)
                    return DatosTratamento(
                        data_inicio=inicio, data_fin=fin, hora=parsear_hora(hora.value),
                        cultivos=[LinhaCultivo(f["cultivo_id"], parsear_decimal(f["superficie"]),
                                               f["estado"])
                                  for f in estado["cultivos"] if f["cultivo_id"] is not None],
                        problemas=[Problema(f["tipo"], f["codigo"])
                                   for f in estado["problemas"] if f["codigo"]],
                        xustificacions=list(xustificacions.value or []),
                        produtos=[LinhaProduto(
                            tipo_produto=f["tipo_produto"], unidade=f["unidade"],
                            num_rexistro=f["num"].strip() or None,
                            nome_comercial=f["nome"].strip() or None,
                            materia_activa=f["materia"].strip() or None,
                            dose=None if f["total"] else parsear_decimal(f["dose"]),
                            cantidade=parsear_decimal(f["dose"]) if f["total"] else None)
                            for f in estado["produtos"] if f["nome"] or f["num"] or f["dose"]],
                        medidas=[LinhaMedida(tipo_medida=f["tipo"],
                                             cantidade=parsear_decimal(f["cantidade"]),
                                             unidade=f["unidade"],
                                             num_rexistro_mdf=f["mdf"].strip() or None)
                                 for f in estado["medidas"] if f["tipo"]],
                        aplicadores=[LinhaAplicador(aplicador.value, maquina.value,
                                                    aplicacion_manual=maquina.value is None)]
                        if aplicador.value else [],
                        asesor=DatosAsesor(asesor.value, data=data_as,
                                           validacion=bool(validacion.value))
                        if asesor.value else None,
                        eficacia=eficacia.value,
                        notas=notas.value or None,
                    )

                @ui.refreshable
                def lista_avisos() -> None:
                    try:
                        d = datos()
                    except ValueError as erro:
                        ui.label(str(erro)).classes("text-sm text-grey-8")
                        return
                    with get_session() as session:
                        horta = session.get(Horta, horta_id)
                        avisos = (comprobar_tratamento(session, horta, d, estado["id"])
                                  if horta else [])
                    if not avisos:
                        ui.label("Sen produtos do rexistro que comprobar.").classes(
                            "text-sm text-grey-8")
                    for a in avisos:
                        cor, icona = {FORTE: ("negative", "error"),
                                      AVISO: ("warning", "warning")}.get(
                            a.nivel, ("primary", "info"))
                        with ui.row().classes("items-start no-wrap gap-2"):
                            ui.icon(icona).classes(f"text-{cor}")
                            ui.label(a.texto).classes("text-sm")

                lista_avisos()
                pasos.on_value_change(
                    lambda e: lista_avisos.refresh() if e.value == _PASO_RESULTADO else None)

                def gardar() -> None:
                    with get_session() as session:
                        actor = usuario_actual(session)
                        if actor is None:
                            pechar_sesion()
                            return

                        def accion() -> None:
                            d = datos()
                            tratamento = (session.get(TratamentoFito, estado["id"])
                                          if estado["id"] else None)
                            if tratamento is None:
                                novo = crear_tratamento_fito(session, actor, horta_id, d)
                                rematar_tarefa(session, actor, estado["tarefa"], novo)
                            else:
                                actualizar_tratamento_fito(session, actor, tratamento, d)

                        ok = executar_accion(session, accion)
                    if ok:
                        ui.navigate.reload()

                with ui.stepper_navigation():
                    ui.button("Gardar", icon="check", on_click=gardar)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
        ui.button("Pechar", on_click=dialogo.close).props("flat")

    def abrir(t: TratamentoFito | None, tarefa: Tarefa | None = None) -> None:
        hoxe = date.today().isoformat()
        estado["tarefa"] = tarefa.id if tarefa else None
        estado["id"] = t.id if t else None
        data_inicio.value = t.data_inicio.isoformat() if t else hoxe
        data_fin.value = t.data_fin.isoformat() if t else hoxe
        estado["inicio"] = data_inicio.value
        hora.value = t.hora.strftime("%H:%M") if t and t.hora else ""
        estado["cultivos"] = [fila_cultivo(c.cultivo_id, _txt(c.superficie_ha),
                                           c.estado_fenoloxico)
                              for c in t.cultivos] if t else []
        estado["problemas"] = [fila_problema(p.tipo, p.codigo) for p in t.problemas] if t else []
        estado["produtos"] = [fila_produto(tipo_produto=p.tipo_produto,
                                           nome=p.nome_comercial or "",
                                           num=p.num_rexistro or "",
                                           materia=p.materia_activa or "",
                                           dose=_txt(p.dose if p.dose is not None
                                                     else p.cantidade),
                                           unidade=p.unidade,
                                           total=p.dose is None and p.cantidade is not None)
                              for p in t.produtos] if t else []
        estado["medidas"] = [fila_medida(m.tipo_medida, _txt(m.cantidade), m.unidade,
                                         m.num_rexistro_mdf or "")
                             for m in t.medidas] if t else []
        estado["cultivos"] = estado["cultivos"] or [
            fila_cultivo(tarefa.cultivo_id if tarefa else None)]
        estado["problemas"] = estado["problemas"] or [fila_problema()]
        estado["produtos"] = estado["produtos"] or [fila_produto()]
        orixinais_t = [(etiqueta, valor) for etiqueta, valor in (
            ("produto", t.orixinal_produto), ("dose", t.orixinal_dose),
            ("aplicador", t.orixinal_aplicador), ("equipo", t.orixinal_equipo),
            ("asesoramento", t.orixinal_asesoramento)) if valor] if t else []
        estado["orixinais"] = " · ".join(f"{e}: {v}" for e, v in orixinais_t)
        xustificacions.value = [x.codigo for x in t.xustificacions
                                if x.codigo in op.xustificacions] if t else []
        a = t.aplicadores[0] if t and t.aplicadores else None
        aplicador.value = _ou_nada(op.aplicadores, a.persoa_id if a else (
            tarefa.persoa_id if tarefa else None))
        maquina.value = _ou_nada(op.maquinas, a.maquina_id if a else None)
        asesor.value = _ou_nada(op.asesores, t.asesor.persoa_id if t and t.asesor else None)
        data_asesor.value = (t.asesor.data.isoformat()
                             if t and t.asesor and t.asesor.data else "")
        validacion.value = bool(t and t.asesor and t.asesor.validacion)
        eficacia.value = _ou_nada(op.eficacias, t.eficacia if t else None)
        notas.value = (t.notas or "") if t else ""
        for refrescar in (filas_cultivos, filas_problemas, filas_produtos, filas_medidas,
                          orixinais):
            refrescar.refresh()
        pasos.set_value("1. Que e onde")
        mirar_tempo()
        dialogo.open()

    return abrir
