"""Diálogo do tratamento fitosanitario, con varias filas de cultivos, problemas, produtos e
medidas, o asesor e os avisos do rexistro do MAPA (deseño 2026-10-25-tratamentos-completos)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from nicegui import app, ui

from horta.db import get_session
from horta.models.horta import Horta
from horta.models.recomendacion import Recomendacion
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TratamentoFito
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fito_consulta import (
    AVISO,
    FORTE,
    comprobar_tratamento,
    dose_etiqueta,
    materia_activa,
)
from horta.services.observacions import (
    NIVEIS,
    UNIDADES_CONTO,
    limiar_para,
    observacions_para_xustificar,
)
from horta.services.recomendacions import (
    actualizar_recomendacion,
    crear_recomendacion,
    ligar_tratamento,
    recomendacion_a_datos,
)
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
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal, parsear_hora
from horta.ui.pasos_tratamento import (
    cantidade_dende_porcentaxe,
    faltan_con_que,
    faltan_por_que,
    faltan_que_e_onde,
    faltan_quen,
    ordenar_problemas,
)
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
    # cultivo → tipo de problema → códigos con usos autorizados nese cultivo (Y5)
    problemas_cultivo: dict[int, dict[str, set[str]]] = field(default_factory=dict)


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


def texto_xustificacion_observacion(
    obs: Any,
    limiar: Any = None,
) -> str:
    """Texto dunha observación para xustificar o tratamento fitosanitario."""
    if obs is None:
        return ""
    if isinstance(obs, dict):
        data = obs.get("data")
        conto = obs.get("conto")
        unidade = obs.get("unidade_conto")
        nivel = obs.get("nivel")
    else:
        data = getattr(obs, "data", None)
        conto = getattr(obs, "conto", None)
        unidade = getattr(obs, "unidade_conto", None)
        nivel = getattr(obs, "nivel", None)

    if data is None:
        return ""
    if isinstance(data, date):
        data_str = data.strftime("%d/%m")
    else:
        d_parseada = parsear_data(str(data))
        data_str = d_parseada.strftime("%d/%m") if d_parseada else str(data)

    partes_detalle: list[str] = []
    if conto is not None:
        if unidade:
            u_str = (UNIDADES_CONTO.get(unidade) or unidade).lower()
            partes_detalle.append(f"{conto:g} {u_str}".strip())
        else:
            partes_detalle.append(f"{conto:g}")
        if nivel:
            nivel_str = NIVEIS.get(nivel, nivel)
            partes_detalle.append(f"({nivel_str})")
    elif nivel:
        nivel_txt = (NIVEIS.get(nivel) or nivel).lower()
        if nivel == "sen":
            partes_detalle.append("sen presenza")
        else:
            partes_detalle.append(f"nivel {nivel_txt}")

    detalle = " ".join(partes_detalle).strip()

    if isinstance(limiar, dict):
        valor_limiar = limiar.get("valor")
    elif hasattr(limiar, "valor"):
        valor_limiar = getattr(limiar, "valor")
    elif isinstance(limiar, (int, float)):
        valor_limiar = limiar
    else:
        valor_limiar = None

    sufixo_limiar = f" (limiar {valor_limiar:g})" if valor_limiar is not None else ""
    if detalle:
        return f"Observación do {data_str}: {detalle}{sufixo_limiar}"
    return f"Observación do {data_str}{sufixo_limiar}"


def crear_dialogo_tratamento(
    horta_id: int, op: OpcionsTratamento
) -> Callable[..., None]:
    """Constrúe o diálogo e devolve a función que o abre (None = tratamento novo)."""
    estado: dict[str, Any] = {"id": None, "cultivos": [], "problemas": [], "produtos": [],
                              "medidas": [], "orixinais": "", "tarefa": None,
                              "modo": "tratamento", "recomendacion_id": None,
                              "visita_id": None}

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
                "materia": "", "dose": "", "unidade": None, "total": False, "etiqueta": ""}
        fila.update(valores)
        fila["tipo_produto"] = _ou_nada(op.tipos_produto, fila["tipo_produto"])
        fila["unidade"] = _ou_nada(op.unidades, fila["unidade"])
        fila["rexistro"] = _ou_nada(op.rexistro, fila["num"])
        return fila

    def cultivo_id_actual() -> int | None:
        return next((f["cultivo_id"] for f in estado["cultivos"] if f["cultivo_id"]), None)

    def primeiro_problema() -> tuple[str, str] | None:
        for f in estado["problemas"]:
            if f.get("codigo"):
                return f.get("tipo", "praga"), f["codigo"]
        return None

    xustificacion_creada = False

    @ui.refreshable
    def xustificacion_observacions() -> None:
        nonlocal xustificacion_creada
        xustificacion_creada = True
        cid = cultivo_id_actual()
        prob = primeiro_problema()
        if cid is None or prob is None:
            return
        try:
            ata = parsear_data(data_inicio.value) or date.today()
        except ValueError:
            ata = date.today()
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                return
            try:
                obs_list = observacions_para_xustificar(
                    session, actor, cid, prob[0], prob[1], ata=ata
                )
            except Exception:
                obs_list = []
            if not obs_list:
                return
            for obs in obs_list:
                limiar = None
                if obs.unidade_conto and obs.metodo:
                    try:
                        limiar = limiar_para(
                            session,
                            horta_id,
                            cid,
                            obs.problema_tipo,
                            obs.problema_codigo,
                            obs.metodo,
                            obs.unidade_conto,
                        )
                    except Exception:
                        limiar = None
                txt = texto_xustificacion_observacion(obs, limiar)
                ui.label(txt).classes("text-caption texto-suave")

    def refrescar_xustificacion() -> None:
        if xustificacion_creada:
            xustificacion_observacions.refresh()

    def actualizar_etiquetas() -> None:
        cid = cultivo_id_actual()
        with get_session() as session:
            for f in estado["produtos"]:
                f["etiqueta"] = dose_etiqueta(session, f["num"], cid)

    def fila_medida(tipo: str | None = None, cantidade: str = "", unidade: str | None = None,
                    mdf: str = "") -> dict[str, Any]:
        return {"tipo": _ou_nada(op.tipos_medida, tipo), "cantidade": cantidade,
                "unidade": _ou_nada(op.unidades, unidade), "mdf": mdf}

    def seguir(faltan: list[str]) -> None:
        """Pasa ao seguinte paso só se non falta nada; se falta, dío todo xunto (Y3)."""
        if faltan:
            ui.notify("Falta: " + "; ".join(faltan), type="warning", multi_line=True)
            return
        pasos.next()

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(46rem, 96vw)"):
        titulo = ui.label("").classes("text-h6 q-mb-sm")
        titulo.set_visibility(False)
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
                    try:
                        d_fin, d_inicio = parsear_data(fin), parsear_data(inicio)
                    except ValueError:
                        d_fin = d_inicio = None
                    antes = d_fin is not None and d_inicio is not None and d_fin < d_inicio
                    if not fin or fin == estado["inicio"] or antes:
                        data_fin.value = inicio
                    estado["inicio"] = inicio

                data_inicio.on_value_change(seguir_inicio)
                ui.label("Cultivos tratados (mesmo cultivo e variedade)").classes("text-bold")

                @ui.refreshable
                def filas_cultivos() -> None:
                    for fila in estado["cultivos"]:
                        with ui.row().classes("w-full items-end gap-2"):
                            def escoller_cultivo(e: Any, f: dict[str, Any] = fila) -> None:
                                f["cultivo_id"] = e.value
                                if not f["superficie"] and e.value in op.superficies:
                                    f["superficie"] = _txt(op.superficies[e.value])
                                mirar_tempo()
                                actualizar_etiquetas()
                                refrescar_xustificacion()

                            def refrescar_cultivos() -> None:
                                filas_cultivos.refresh()
                                refrescar_xustificacion()

                            ui.select(op.cultivos, label="Cultivo e parcela",
                                      with_input=True, on_change=escoller_cultivo).bind_value(
                                fila, "cultivo_id").classes("grow")
                            ui.input("Superficie (ha)").bind_value(fila, "superficie").classes(
                                "w-28")
                            ui.select(op.estados, label="Estado fenolóxico").bind_value(
                                fila, "estado").classes("w-40")
                            _papeleira(estado["cultivos"], fila, refrescar_cultivos)

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

                    def seguir_paso_1() -> None:
                        # Os problemas do cultivo escollido van primeiro (Y5)
                        filas_problemas.refresh()
                        refrescar_xustificacion()
                        fin_val = (
                            data_fin.value
                            or (data_inicio.value if estado.get("modo") == "recomendacion" else "")
                        )
                        seguir(faltan_que_e_onde(data_inicio.value, fin_val,
                                                 estado["cultivos"]))

                    ui.button("Seguinte", on_click=seguir_paso_1)
            with ui.step("2. Por que"):

                @ui.refreshable
                def filas_problemas() -> None:
                    def refrescar_problemas() -> None:
                        filas_problemas.refresh()
                        refrescar_xustificacion()

                    for fila in estado["problemas"]:
                        with ui.row().classes("w-full items-end gap-2"):

                            def cambiar_tipo(e: Any, f: dict[str, Any] = fila) -> None:
                                f["tipo"], f["codigo"] = e.value, None
                                refrescar_problemas()

                            def escoller_problema(e: Any, f: dict[str, Any] = fila) -> None:
                                f["codigo"] = e.value
                                refrescar_xustificacion()

                            ui.select(ETIQUETA_PROBLEMA, value=fila["tipo"], label="Tipo",
                                      on_change=cambiar_tipo).classes("w-48")
                            do_cultivo = set().union(*(
                                op.problemas_cultivo.get(c["cultivo_id"], {}).get(fila["tipo"],
                                                                                 set())
                                for c in estado["cultivos"]))
                            ui.select(ordenar_problemas(op.problemas[fila["tipo"]], do_cultivo,
                                                        fila["codigo"]),
                                      label="Problema", with_input=True,
                                      on_change=escoller_problema).bind_value(
                                fila, "codigo").classes("grow")
                            _papeleira(estado["problemas"], fila, refrescar_problemas)

                    def engadir() -> None:
                        estado["problemas"].append(fila_problema())
                        refrescar_problemas()

                    ui.button("Engadir problema", icon="add", on_click=engadir).props(
                        "flat dense")

                filas_problemas()
                xustificacion_observacions()
                xustificacions = ui.select(op.xustificacions, label="Xustificacións",
                                           multiple=True).classes("w-full").props("use-chips")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=lambda: seguir(faltan_por_que(
                        estado["problemas"], xustificacions.value)))
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
                                        f["etiqueta"] = dose_etiqueta(
                                            session, e.value, cultivo_id_actual())
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
                            ui.label().classes("text-caption texto-suave").bind_text_from(
                                fila, "etiqueta").bind_visibility_from(
                                fila, "etiqueta", backward=bool)
                            ui.checkbox("É a cantidade total, non a dose por hectárea"
                                        ).bind_value(fila, "total")
                            with ui.expansion("A etiqueta dá a dose en % (mochila)").classes(
                                    "w-full"):
                                with ui.row().classes("w-full items-end gap-2"):
                                    pct = ui.input("% da etiqueta").classes("w-28")
                                    caldo = ui.input("Litros de caldo").classes("w-32")
                                    en = ui.select({"4": "L de produto", "5": "kg de produto"},
                                                   value="4").classes("w-36")

                                    def calcular(f: dict[str, Any] = fila, p: Any = pct,
                                                 c: Any = caldo, u: Any = en) -> None:
                                        # Y4: «0,5 %» en 16 L de caldo son 0,08 L de produto
                                        porcentaxe = parsear_decimal(p.value)
                                        litros = parsear_decimal(c.value)
                                        if not porcentaxe or not litros:
                                            ui.notify("Pon a % e os litros de caldo",
                                                      type="warning")
                                            return
                                        f["dose"] = _txt(cantidade_dende_porcentaxe(
                                            porcentaxe, litros)).replace(".", ",")
                                        f["total"], f["unidade"] = True, u.value

                                    ui.button("Calcular", on_click=calcular).props("flat")

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
                    ui.button("Seguinte", on_click=lambda: seguir(faltan_con_que(
                        estado["produtos"], estado["medidas"])))
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("4. Quen"):
                aplicador = ui.select(op.aplicadores, label="Aplicador").classes("w-full")
                maquina = ui.select(op.maquinas, label="Máquina (baleiro se é manual)"
                                    ).classes("w-full")
                horas = ui.input("Horas de traballo").classes("w-full")
                asesor = ui.select(op.asesores, label="Asesor (opcional)",
                                   clearable=True).classes("w-full")
                data_asesor = campo_data("Data do asesoramento")
                validacion = ui.checkbox("A persoa asesora validou o tratamento")
                for campo in (asesor, data_asesor, validacion):
                    campo.set_visibility(bool(op.asesores))
                with ui.stepper_navigation():
                    def seguir_paso_4() -> None:
                        if estado.get("modo") == "recomendacion":
                            if not asesor.value:
                                ui.notify("Escolle unha persoa asesora", type="warning")
                                return
                            pasos.next()
                        else:
                            seguir(faltan_quen(aplicador.value))

                    ui.button("Seguinte", on_click=seguir_paso_4)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step(_PASO_RESULTADO):
                eficacia = ui.select(op.eficacias, label="Eficacia").classes("w-full")
                notas = ui.textarea("Notas").classes("w-full")
                ui.label("Comprobación co rexistro do MAPA (a etiqueta é a referencia legal)"
                         ).classes("text-bold")

                def datos() -> DatosTratamento:
                    inicio = parsear_data(data_inicio.value)
                    fin = parsear_data(data_fin.value)
                    if estado.get("modo") == "recomendacion" and fin is None:
                        fin = inicio
                    if inicio is None or fin is None:
                        raise OperacionNonPermitidaError("Indica as datas de inicio e fin")
                    e_rec = estado.get("modo") == "recomendacion"
                    data_as = parsear_data(data_asesor.value) if not e_rec else inicio
                    val_as = bool(validacion.value) if not e_rec else True
                    return DatosTratamento(
                        data_inicio=inicio, data_fin=fin,
                        hora=parsear_hora(hora.value) if not e_rec else None,
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
                        aplicadores=[LinhaAplicador(
                            aplicador.value, maquina.value, aplicacion_manual=maquina.value is None,
                            horas_utilizacion=parsear_decimal(horas.value))]
                        if (aplicador.value and not e_rec) else [],
                        asesor=DatosAsesor(asesor.value, data=data_as,
                                           validacion=val_as)
                        if asesor.value else None,
                        eficacia=eficacia.value if not e_rec else None,
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
                    lambda e: lista_avisos.refresh() if e.value == _PASO_RESULTADO else (
                        refrescar_xustificacion() if e.value == "2. Por que" else None
                    )
                )

                def gardar() -> None:
                    with get_session() as session:
                        actor = usuario_actual(session)
                        if actor is None:
                            pechar_sesion()
                            return

                        def accion() -> None:
                            d = datos()
                            if estado.get("modo") == "recomendacion":
                                if d.asesor is None or not d.asesor.persoa_id:
                                    raise OperacionNonPermitidaError(
                                        "Escolle unha persoa asesora da explotación"
                                    )
                                valida_ata = (
                                    d.data_fin if d.data_fin != d.data_inicio else None
                                )
                                rec_id = estado.get("recomendacion_id")
                                if rec_id is None:
                                    crear_recomendacion(
                                        session,
                                        actor,
                                        horta_id,
                                        asesor_persoa_id=d.asesor.persoa_id,
                                        data=d.data_inicio,
                                        cultivos=d.cultivos,
                                        problemas=d.problemas,
                                        xustificacions=d.xustificacions,
                                        produtos=d.produtos,
                                        medidas=d.medidas,
                                        valida_ata=valida_ata,
                                        observacions=d.notas,
                                        visita_id=estado.get("visita_id"),
                                    )
                                else:
                                    rec = session.get(Recomendacion, rec_id)
                                    if rec is None:
                                        raise OperacionNonPermitidaError(
                                            "A recomendación xa non existe"
                                        )
                                    visita_kw = {}
                                    if estado.get("visita_id") is not None:
                                        visita_kw["visita_id"] = estado["visita_id"]
                                    actualizar_recomendacion(
                                        session,
                                        actor,
                                        rec,
                                        asesor_persoa_id=d.asesor.persoa_id,
                                        data=d.data_inicio,
                                        cultivos=d.cultivos,
                                        problemas=d.problemas,
                                        xustificacions=d.xustificacions,
                                        produtos=d.produtos,
                                        medidas=d.medidas,
                                        valida_ata=valida_ata,
                                        observacions=d.notas,
                                        **visita_kw,
                                    )
                            else:
                                tratamento = (session.get(TratamentoFito, estado["id"])
                                              if estado["id"] else None)
                                if tratamento is None:
                                    novo = crear_tratamento_fito(session, actor, horta_id, d)
                                    rec_id = estado.get("recomendacion_id")
                                    if rec_id:
                                        rec = session.get(Recomendacion, rec_id)
                                        if rec is not None:
                                            ligar_tratamento(session, actor, rec, novo)
                                    rematar_tarefa(session, actor, estado["tarefa"], novo)
                                else:
                                    actualizar_tratamento_fito(session, actor, tratamento, d)

                        ok = executar_accion(session, accion)
                    if ok:
                        if estado.get("modo") == "recomendacion":
                            dialogo.close()
                            app.storage.user["aviso"] = "Recomendación gardada"
                            ui.navigate.reload()
                        else:
                            recargar_apuntado("tratamento", data_inicio.value)

                with ui.stepper_navigation():
                    ui.button("Gardar", icon="check", on_click=gardar)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
        ui.button("Pechar", on_click=dialogo.close).props("flat")

    def abrir(
        t: TratamentoFito | None = None,
        tarefa: Tarefa | None = None,
        recomendacion: Recomendacion | None = None,
        modo: str = "tratamento",
        visita_id: int | None = None,
    ) -> None:
        hoxe = date.today().isoformat()
        estado["modo"] = modo
        estado["tarefa"] = tarefa.id if tarefa else None
        estado["id"] = t.id if t else None
        estado["recomendacion_id"] = recomendacion.id if recomendacion else None
        estado["visita_id"] = (
            visita_id if visita_id is not None else (
                recomendacion.visita_id if recomendacion else None
            )
        )

        e_rec = modo == "recomendacion"
        if e_rec:
            titulo.text = "Recomendación da persoa asesora"
            titulo.set_visibility(True)
            data_inicio._props["label"] = "Data da recomendación"
            data_fin._props["label"] = "Válida ata"
        else:
            titulo.text = ""
            titulo.set_visibility(False)
            data_inicio._props["label"] = "Data de inicio"
            data_fin._props["label"] = "Data de fin"
        data_inicio.update()
        data_fin.update()

        aplicador.set_visibility(not e_rec)
        maquina.set_visibility(not e_rec)
        horas.set_visibility(not e_rec)
        eficacia.set_visibility(not e_rec)
        hora.set_visibility(not e_rec)
        data_asesor.set_visibility(not e_rec and bool(op.asesores))
        validacion.set_visibility(not e_rec and bool(op.asesores))
        asesor.set_visibility(True if e_rec else bool(op.asesores))
        asesor._props["label"] = "Asesor" if e_rec else "Asesor (opcional)"
        asesor.update()

        if recomendacion is not None:
            d = recomendacion_a_datos(recomendacion)
            if e_rec:
                data_inicio.value = d.data_inicio.isoformat()
                data_fin.value = (recomendacion.valida_ata or d.data_inicio).isoformat()
            else:
                data_inicio.value = hoxe
                data_fin.value = hoxe
            estado["inicio"] = data_inicio.value
            hora.value = ""
            estado["cultivos"] = [
                fila_cultivo(c.cultivo_id, _txt(c.superficie_ha), c.estado_fenoloxico)
                for c in d.cultivos
            ]
            estado["problemas"] = [
                fila_problema(p.tipo, p.codigo) for p in d.problemas
            ]
            estado["produtos"] = [
                fila_produto(
                    tipo_produto=p.tipo_produto,
                    nome=p.nome_comercial or "",
                    num=p.num_rexistro or "",
                    materia=p.materia_activa or "",
                    dose=_txt(p.dose if p.dose is not None else p.cantidade),
                    unidade=p.unidade,
                    total=p.dose is None and p.cantidade is not None,
                )
                for p in d.produtos
            ]
            estado["medidas"] = [
                fila_medida(
                    m.tipo_medida, _txt(m.cantidade), m.unidade, m.num_rexistro_mdf or ""
                )
                for m in d.medidas
            ]
            estado["orixinais"] = ""
            xustificacions.value = [x for x in d.xustificacions if x in op.xustificacions]
            aplicador.value = None
            maquina.value = None
            horas.value = ""
            asesor.value = _ou_nada(op.asesores, recomendacion.asesor_persoa_id)
            data_asesor.value = recomendacion.data.isoformat()
            validacion.value = True
            eficacia.value = None
            notas.value = d.notas or ""
        elif t is not None:
            data_inicio.value = t.data_inicio.isoformat()
            data_fin.value = t.data_fin.isoformat()
            estado["inicio"] = data_inicio.value
            hora.value = t.hora.strftime("%H:%M") if t.hora else ""
            estado["cultivos"] = [
                fila_cultivo(c.cultivo_id, _txt(c.superficie_ha), c.estado_fenoloxico)
                for c in t.cultivos
            ]
            estado["problemas"] = [fila_problema(p.tipo, p.codigo) for p in t.problemas]
            estado["produtos"] = [
                fila_produto(
                    tipo_produto=p.tipo_produto,
                    nome=p.nome_comercial or "",
                    num=p.num_rexistro or "",
                    materia=p.materia_activa or "",
                    dose=_txt(p.dose if p.dose is not None else p.cantidade),
                    unidade=p.unidade,
                    total=p.dose is None and p.cantidade is not None,
                )
                for p in t.produtos
            ]
            estado["medidas"] = [
                fila_medida(
                    m.tipo_medida, _txt(m.cantidade), m.unidade, m.num_rexistro_mdf or ""
                )
                for m in t.medidas
            ]
            orixinais_t = [
                (etiqueta, valor)
                for etiqueta, valor in (
                    ("produto", t.orixinal_produto),
                    ("dose", t.orixinal_dose),
                    ("aplicador", t.orixinal_aplicador),
                    ("equipo", t.orixinal_equipo),
                    ("asesoramento", t.orixinal_asesoramento),
                )
                if valor
            ]
            estado["orixinais"] = " · ".join(f"{e}: {v}" for e, v in orixinais_t)
            xustificacions.value = [
                x.codigo for x in t.xustificacions if x.codigo in op.xustificacions
            ]
            a = t.aplicadores[0] if t.aplicadores else None
            aplicador.value = _ou_nada(
                op.aplicadores, a.persoa_id if a else (tarefa.persoa_id if tarefa else None)
            )
            maquina.value = _ou_nada(op.maquinas, a.maquina_id if a else None)
            horas.value = f"{a.horas_utilizacion:g}" if a and a.horas_utilizacion else ""
            asesor.value = _ou_nada(op.asesores, t.asesor.persoa_id if t.asesor else None)
            data_asesor.value = (
                t.asesor.data.isoformat() if t.asesor and t.asesor.data else ""
            )
            validacion.value = bool(t.asesor and t.asesor.validacion)
            eficacia.value = _ou_nada(op.eficacias, t.eficacia if t else None)
            notas.value = t.notas or ""
        else:
            data_inicio.value = hoxe
            data_fin.value = hoxe
            estado["inicio"] = data_inicio.value
            hora.value = ""
            estado["cultivos"] = []
            estado["problemas"] = []
            estado["produtos"] = []
            estado["medidas"] = []
            estado["orixinais"] = ""
            xustificacions.value = []
            aplicador.value = _ou_nada(
                op.aplicadores, tarefa.persoa_id if tarefa else None
            )
            maquina.value = None
            horas.value = ""
            asesor.value = None
            data_asesor.value = ""
            validacion.value = False
            eficacia.value = None
            notas.value = ""

        estado["cultivos"] = estado["cultivos"] or [
            fila_cultivo(tarefa.cultivo_id if tarefa else None)
        ]
        estado["problemas"] = estado["problemas"] or [fila_problema()]
        estado["produtos"] = estado["produtos"] or [fila_produto()]
        actualizar_etiquetas()
        for refrescar in (
            filas_cultivos,
            filas_problemas,
            filas_produtos,
            filas_medidas,
            orixinais,
        ):
            refrescar.refresh()
        refrescar_xustificacion()
        pasos.set_value("1. Que e onde")
        mirar_tempo()
        dialogo.open()

    return abrir
