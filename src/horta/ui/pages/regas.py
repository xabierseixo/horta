"""Sección Rega: cada rega, nunha ou varias leiras (CUE bloque 10). Baixa lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, datetime

from nicegui import ui

from horta.db import get_session
from horta.models.parcela import Parcela
from horta.models.rega import Rega
from horta.models.tarefa import Tarefa
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.maquinaria import listar_maquinas
from horta.services.necesidades_rega import necesidades_horta
from horta.services.persoas import listar_quen
from horta.services.regas import (
    UNIDADES_AUGA,
    DatosRega,
    actualizar_rega,
    crear_rega,
    dar_de_baixa_rega,
    listar_regas,
    litros_estimados,
    ultimo_sistema_rega,
)
from horta.services.sensores import consumo_periodo, listar_sensores
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.leiras import leiras_escollidas
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.necesidades_rega import buscar_humidade_chan, texto_humidade_chan
from horta.ui.numeros import formatar_decimal, parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA
from horta.ui.tempo import EtiquetaTempo


def seccion_regas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        regas = listar_regas(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        todos_cultivos = listar_cultivos(session, actor, horta_id)
        cultivos = {
            c.id: f"{nome_cultivo(c)} — {parcelas.get(c.parcela_id, '')}"
            for c in todos_cultivos
        }
        cultivos_por_id = {c.id: c for c in todos_cultivos}
        sistemas = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "sistema_rega")}
        unidades_cat = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                        for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat.get(c, c) for c in UNIDADES_AUGA}
        necesidades = necesidades_horta(session, actor, horta_id)
        humidades_cultivos = {}
        for c_id, c_obj in cultivos_por_id.items():
            h_info = buscar_humidade_chan(session, actor, c_id, c_obj.parcela_id)
            if h_info:
                humidades_cultivos[c_id] = h_info

    with ui.column().classes("tarxeta w-full gap-1 q-mb-md"):
        ui.label("Necesidades de rega (últimos 7 días)").classes(
            "text-subtitle1 text-weight-bold"
        )
        precisan_auga = [n for n in necesidades if n.estado == "ok" and n.falta_mm > 0]
        if precisan_auga:
            for n in precisan_auga:
                nome_leira = cultivos.get(n.cultivo_id, "")
                falta = formatar_decimal(round(n.falta_mm, 1))
                h_info = humidades_cultivos.get(n.cultivo_id)
                txt_h = f" · {texto_humidade_chan(h_info[0], h_info[1])}" if h_info else ""
                ui.label(f"{nome_leira}: faltan uns {falta} l/m²{txt_h}")
        else:
            ui.label("Os cultivos de regadío teñen auga dabondo estes días")

        outros = [n for n in necesidades if n.estado not in ("ok", "secano")]
        if outros:
            nomes = ", ".join(
                dict.fromkeys(
                    nome_cultivo(cultivos_por_id[n.cultivo_id])
                    for n in outros
                    if n.cultivo_id in cultivos_por_id
                )
            )
            ui.label(f"Sen cálculo: {nomes} (mira a ficha de cada cultivo)").classes(
                "text-caption texto-suave"
            )

        ui.label(
            "ET0 de MeteoGalicia e coeficientes FAO-56, o método do SiAR (Ministerio)."
        ).classes("text-caption texto-suave")

    filas = [{
        "id": r.id,
        "data": f"{r.data_inicio:%d/%m/%Y}",
        "cultivo": ", ".join(cultivos.get(le.cultivo_id, "") for le in r.leiras),
        "sistema": sistemas.get(r.sistema_rega, r.sistema_rega) if r.sistema_rega else "",
        "auga": f"{r.cantidade:g} {unidades.get(r.unidade, '')}" if r.cantidade else "",
    } for r in regas]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("sistema", "Sistema"),
            ("auga", "Auga"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai regas" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "data", ["cultivo", "auga"], accions_tarxeta)

    if not pode_editar:
        return
    abrir = dialogo_rega(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha rega na táboa", type="warning")
            return
        with get_session() as session:
            r = session.get(Rega, taboa.selected[0]["id"])
            if r is not None:
                _ = r.boas_practicas
                abrir(r)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha rega na táboa", type="warning")
            return
        rega_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                r = session.get(Rega, rega_id)
                if actor_actual is None or r is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_rega(
                    session, actor_actual, r))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta rega? Non se borra: consérvase no histórico.", confirmar)

    accions_tarxeta += [("Editar", "edit", editar),
                        ("Dar de baixa", "archive", dar_de_baixa)]

    with ui.row():
        ui.button("Apuntar rega", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline").classes(
            "so-ordenador"
        )
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline").classes(
            "so-ordenador"
        )


def dialogo_rega(horta_id: int) -> Callable[[Rega | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha rega e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{nome_cultivo(c)} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        sistemas = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "sistema_rega")}
        orixes = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                  for v in valores_vixentes(session, "orixe_auga")}
        unidades_cat = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                        for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat.get(c, c) for c in UNIDADES_AUGA}
        practicas = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "boas_practicas")
                     if "rega" in (v.categoria or "")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        contadores = [
            s for s in listar_sensores(session, actor, horta_id, so_activos=True)
            if s.tipo == "contador_auga"
        ]

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with (ui.dialog().props("persistent") as calculadora,
          ui.card().style("width: min(28rem, 94vw)")):
        ui.label("Calcular os litros").classes("text-h6")
        ui.label("Con mangueira ou goteo:").classes("text-caption")
        with ui.row().classes("w-full no-wrap"):
            minutos = ui.input("Minutos").classes("col")
            litros_minuto = ui.input("Litros por minuto").classes("col")
        ui.label("Ou con regadeira:").classes("text-caption")
        with ui.row().classes("w-full no-wrap"):
            regadeiras = ui.input("Regadeiras").classes("col")
            litros_regadeira = ui.input("Litros de cada unha").classes("col")

        def usar() -> None:
            litros = litros_estimados(
                parsear_decimal(minutos.value), parsear_decimal(litros_minuto.value),
                parsear_decimal(regadeiras.value), parsear_decimal(litros_regadeira.value))
            if litros is None:
                ui.notify("Enche minutos e litros por minuto, ou regadeiras e litros",
                          type="warning")
                return
            cantidade.value, unidade.value = f"{litros:g}", "4"
            calculadora.close()

        with ui.row():
            ui.button("Usar estes litros", icon="check", on_click=usar)
            ui.button("Cancelar", on_click=calculadora.close).props("flat")

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar rega").classes("text-h6")
        if not sistemas:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
        cultivo = ui.select(cultivos, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data_inicio = campo_data("Data", date.today().isoformat())
        tempo = EtiquetaTempo(horta_id, "rega")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo; só cunha leira)")
        sistema = ui.select(sistemas, label="Como se rega").classes("w-full")
        with ui.row().classes("w-full no-wrap items-center"):
            cantidade = ui.input("Auga").classes("col")
            unidade = ui.select(unidades, value="4", label="Unidade").classes("col")
        with ui.row().classes("gap-2 items-center"):
            ui.button("Non sei os litros", icon="calculate", on_click=calculadora.open).props(
                "flat dense")
            if contadores:
                def coller_do_contador() -> None:
                    inicio = parsear_data(data_inicio.value)
                    if inicio is None:
                        ui.notify("Indica a data de inicio", type="warning")
                        return
                    fin = parsear_data(data_fin.value) or inicio
                    dt_desde = datetime(inicio.year, inicio.month, inicio.day, 0, 0, 0)
                    dt_ata = datetime(fin.year, fin.month, fin.day, 23, 59, 59)
                    with get_session() as s:
                        act = usuario_actual(s)
                        if act is None:
                            pechar_sesion()
                            return
                        consumo = consumo_periodo(
                            s, act, contadores[0].id, dt_desde, dt_ata
                        )
                    if consumo is None:
                        ui.notify(
                            "Non hai lecturas do contador nese período",
                            type="warning",
                        )
                        return
                    cantidade.value = f"{consumo:g}"
                    unidade.value = "3"

                ui.button(
                    "Coller do contador",
                    icon="sensors",
                    on_click=coller_do_contador,
                ).props("flat dense")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            orixe = ui.select(orixes, label="De onde vén a auga (baleiro = a da parcela)",
                              clearable=True).classes("w-full")
            contador = ui.input("Nº de contador").classes("w-full")
            boas = ui.select(practicas, multiple=True, label="Boas prácticas").classes(
                "w-full").props("use-chips")
            notas = ui.textarea("Notas").classes("w-full")

        def cambiar_leiras() -> None:
            superficie.set_visibility(len(cultivo.value or []) == 1)
            if cultivo.value and sistema.value is None:
                with get_session() as session:
                    sistema.value = ultimo_sistema_rega(session, cultivo.value[0])
            tempo.actualizar(data_inicio.value, cultivo.value)

        cultivo.on_value_change(cambiar_leiras)
        data_inicio.on_value_change(lambda: tempo.actualizar(data_inicio.value, cultivo.value))

        def gardar() -> None:
            if not cultivo.value:
                ui.notify("Escolle as leiras", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    inicio = parsear_data(data_inicio.value)
                    if inicio is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosRega(
                        leiras=leiras_escollidas(cultivo.value, superficie.ha),
                        data_inicio=inicio, data_fin=parsear_data(data_fin.value),
                        sistema_rega=sistema.value,
                        cantidade=parsear_decimal(cantidade.value),
                        unidade=unidade.value or "4", orixe_auga=orixe.value,
                        num_contador=contador.value or None,
                        boas_practicas=list(boas.value or []), notas=notas.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value)
                    existente = session.get(Rega, editando["id"]) if editando["id"] else None
                    if existente is None:
                        novo = crear_rega(session, actor_actual, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_rega(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("rega", data_inicio.value)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(r: Rega | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = r.id if r else None
        titulo.text = "Editar rega" if r else "Apuntar rega"
        sistema.value = r.sistema_rega if r else None
        cultivo.value = ([le.cultivo_id for le in r.leiras] if r else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
        data_inicio.value = (r.data_inicio if r else date.today()).isoformat()
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{r.horas:g}" if r and r.horas else ""
        maquina.value = r.maquina_id if r and r.maquina_id in maquinas else None
        superficie.establecer(r.leiras[0].superficie_ha if r and len(r.leiras) == 1 else None)
        cambiar_leiras()
        cantidade.value = f"{r.cantidade:g}" if r and r.cantidade else ""
        unidade.value = r.unidade if r else "4"
        orixe.value = r.orixe_auga if r else None
        contador.value = (r.num_contador or "") if r else ""
        boas.value = [b.codigo for b in r.boas_practicas] if r else []
        notas.value = (r.notas or "") if r else ""
        dialogo.open()

    return abrir
