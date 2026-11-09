"""Sección Colleitas: cada colleita co seu lote. Baixa lóxica, como os tratamentos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.tarefa import Tarefa
from horta.services.catalogos import valores_vixentes
from horta.services.colleitas import (
    UNIDADES_COLLEITA,
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    crear_colleitas,
    dar_de_baixa_colleita,
    listar_colleitas,
    propor_lote,
    rendemento_kg_ha,
)
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.estimacions import (
    borrar_estimacion,
    crear_estimacion,
    kg_ha_por_mostraxe,
    listar_estimacions,
    resumo_estimacion,
)
from horta.services.fito_consulta import aviso_prazo_colleita
from horta.services.lotes import listar_lotes, resumo_lotes
from horta.services.persoas import listar_quen
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import formatar_decimal, formatar_enteiro, parsear_data, parsear_decimal
from horta.ui.pages.lotes import dialogo_saida
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA


def seccion_colleitas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        colleitas = listar_colleitas(session, actor, horta_id)
        queda = resumo_lotes(session, actor, horta_id)
        unidades_lote = {lo.id: lo.unidade for lo in listar_lotes(session, actor, horta_id)}
        cultivos = listar_cultivos(session, actor, horta_id)
        destinos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "destino_colleita")}
        con_colleitas = {c.cultivo_id for c in colleitas}
        rendementos = {c.id: rendemento_kg_ha(session, actor, c.id)
                       for c in cultivos if c.id in con_colleitas}

    nomes_cultivo = {c.id: nome_cultivo(c) for c in cultivos}
    filas = [
        {
            "id": c.id,
            "data": f"{c.data:%d/%m/%Y}",
            "cultivo": nomes_cultivo.get(c.cultivo_id, ""),
            "cantidade": f"{c.cantidade:g} {c.unidade}",
            "lote": c.lote,
        "queda": (f"{queda[c.lote_id][2]:g} {unidades_lote[c.lote_id]}"
                  if c.lote_id in queda else ""),
            "destino": destinos.get(c.destino_colleita or "", ""),
        }
        for c in colleitas
    ]
    abrir_estimacion = dialogo_estimacion(horta_id, pode_editar)

    with ui.row().classes("gap-4 items-center"):
        for cultivo_id, kg_ha in rendementos.items():
            if kg_ha is not None:
                with ui.row().classes("items-center gap-1"):
                    ui.label(
                        f"{nomes_cultivo[cultivo_id]}: {formatar_enteiro(kg_ha)} kg/ha"
                    ).classes("text-body2")
                    ui.button(
                        "Estimación",
                        on_click=lambda cid=cultivo_id: abrir_estimacion(cid),
                    ).props("flat dense")
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("cantidade", "Cantidade"),
            ("lote", "Lote"), ("queda", "Queda"), ("destino", "Destino"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "data", ["cultivo", "cantidade"], accions_tarxeta)

    if not pode_editar:
        return

    abrir = dialogo_colleita(horta_id)

    abrir_saida = dialogo_saida(horta_id)

    def vender() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un rexistro na táboa", type="warning")
            return
        c_escollida = next(x for x in colleitas if x.id == taboa.selected[0]["id"])
        abrir_saida(None, None, c_escollida.lote_id, "venda")

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        abrir(next(x for x in colleitas if x.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        colleita_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                colleita = session.get(Colleita, colleita_id)
                if actor is None or colleita is None:
                    return
                ok = executar_accion(
                    session, lambda: dar_de_baixa_colleita(session, actor, colleita)
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta colleita? Non se borra: consérvase no histórico.", confirmar
        )

    accions_tarxeta += [("Vender", "sell", vender),
                        ("Editar", "edit", editar),
                        ("Dar de baixa", "archive", dar_de_baixa)]

    with ui.row():
        ui.button("Apuntar colleita", icon="add", on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador"):
            ui.button("Vender", icon="sell", on_click=vender).props("outline")
            ui.button("Editar", icon="edit", on_click=editar).props("outline")
            ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_colleita(horta_id: int) -> Callable[[Colleita | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha colleita e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        nomes_cultivo = {c.id: nome_cultivo(c)
                         for c in listar_cultivos(session, actor, horta_id)}
        destinos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "destino_colleita")}
        restos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                  for v in valores_vixentes(session, "destino_restos")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("Apuntar colleita").classes("text-h6")
        # Varias leiras dunha vez: unha colleita por leira, coa súa cantidade e no mesmo lote
        cultivo = ui.select(nomes_cultivo, label="Leiras (unha ou varias)", with_input=True,
                            multiple=True, value=[]).classes("w-full").props("use-chips")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
        cantidades: dict[int, ui.input] = {}

        @ui.refreshable
        def cantidades_por_leira() -> None:
            cantidades.clear()
            if len(cultivo.value or []) > 1:
                ui.label("Canto se colleu en cada leira").classes("text-caption")
                for cultivo_id in cultivo.value:
                    cantidades[cultivo_id] = ui.input(nomes_cultivo.get(cultivo_id, "")).classes(
                        "w-full")

        cantidades_por_leira()
        lote = ui.input("Lote (un que xa exista do mesmo cultivo súmase a el)").classes("w-full")
        superficie = CampoSuperficie("Superficie colleitada (baleiro = a do cultivo)")
        data_fin = campo_data("Data de fin (se durou máis dun día)")
        horas = ui.input("Horas de traballo").classes("w-full")
        destino = ui.select(destinos, label="Finalidade (só viño ou procesado industrial)",
                            clearable=True).classes("w-full")
        destino_restos = ui.select(restos, label="Que se fai cos restos", clearable=True).classes(
            "w-full")
        sementes = ui.checkbox("Obtéñense sementes para sementar")
        plantas = ui.checkbox("Obtéñense plantas ou plantóns")
        sen_colleita = ui.checkbox("Sen colleita por razóns ambientais")
        restos_solo = ui.checkbox("Os restos quedan no chan")
        notas = ui.textarea("Notas").classes("w-full")

        def propor() -> None:
            varias = len(cultivo.value or []) > 1
            cantidade.set_visibility(not varias)
            superficie.set_visibility(len(cultivo.value or []) == 1)
            cantidades_por_leira.refresh()
            if editando["id"] is not None or not cultivo.value:
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    return
                lote.value = propor_lote(session, actor, cultivo.value[0],
                                         parsear_data(data.value) or date.today())

        cultivo.on_value_change(propor)
        aviso_prazo = ui.label().classes("text-negative text-sm")

        def comprobar_prazo() -> None:
            dia = parsear_data(data.value) if data.value else None
            if not cultivo.value or dia is None:
                aviso_prazo.text = ""
                return
            with get_session() as session:
                aviso_prazo.text = " ".join(
                    aviso for c in cultivo.value
                    if (aviso := aviso_prazo_colleita(session, c, dia))) or ""

        cultivo.on_value_change(comprobar_prazo)
        data.on_value_change(comprobar_prazo)

        def gardar() -> None:
            if not cultivo.value:
                ui.notify("Escolle as leiras", type="negative")
                return
            if editando["id"] is not None and len(cultivo.value) > 1:
                ui.notify("Unha colleita apuntada é dunha leira: para máis, apunta outra",
                          type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    datos = DatosColleita(
                        cultivo_id=cultivo.value[0],
                        data=parsear_data(data.value) or date.today(),
                        cantidade=parsear_decimal(cantidade.value) or 0,
                        unidade=unidade.value,
                        lote=lote.value or "",
                        superficie_ha=superficie.ha,
                        destino_colleita=destino.value,
                        destino_restos=destino_restos.value,
                        notas=notas.value or None,
                        data_fin=parsear_data(data_fin.value),
                        obten_sementes=sementes.value,
                        obten_plantas=plantas.value,
                        sen_colleita_ambiental=sen_colleita.value,
                        restos_no_solo=restos_solo.value,
                        persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value),
                    )
                    if editando["id"] is None and len(cultivo.value) > 1:
                        novas = crear_colleitas(session, actor, datos, {
                            c: parsear_decimal(entrada.value) or 0
                            for c, entrada in cantidades.items()})
                        rematar_tarefa(session, actor, editando["tarefa"], novas[0])
                    elif editando["id"] is None:
                        novo = crear_colleita(session, actor, datos)
                        rematar_tarefa(session, actor, editando["tarefa"], novo)
                    else:
                        colleita = session.get(Colleita, editando["id"])
                        if colleita is not None:
                            actualizar_colleita(session, actor, colleita, datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("colleita", data.value)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(c: Colleita | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = c.id if c else None
        titulo.text = "Editar colleita" if c else "Apuntar colleita"
        cultivo.value = ([c.cultivo_id] if c else
                         [tarefa.cultivo_id] if tarefa and tarefa.cultivo_id else [])
        data.value = (c.data if c else date.today()).isoformat()
        persoa.value = (c.persoa_id if c.persoa_id in persoas else None) if c else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{c.horas:g}" if c and c.horas else ""
        cantidade.value = f"{c.cantidade:g}" if c else ""
        unidade.value = c.unidade if c else "kg"
        lote.value = c.lote if c else ""
        superficie.establecer(c.superficie_ha if c else None)
        destino.value = c.destino_colleita if c else None
        destino_restos.value = c.destino_restos if c else None
        notas.value = (c.notas or "") if c else ""
        data_fin.value = c.data_fin.isoformat() if c and c.data_fin else ""
        sementes.value = bool(c and c.obten_sementes)
        plantas.value = bool(c and c.obten_plantas)
        sen_colleita.value = bool(c and c.sen_colleita_ambiental)
        restos_solo.value = bool(c and c.restos_no_solo)
        propor()
        if c:
            lote.value = c.lote
        dialogo.open()

    return abrir


def dialogo_estimacion(horta_id: int, pode_editar: bool) -> Callable[[int], None]:
    """Constrúe o diálogo de estimación da colleita para un cultivo."""
    cultivo_actual: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(38rem, 94vw)"):
        with ui.row().classes("w-full items-center justify-between"):
            titulo = ui.label("Estimación da colleita").classes("text-h6")
            ui.button(icon="close", on_click=dialogo.close).props("flat round dense")

        @ui.refreshable
        def contido_dialogo() -> None:
            cid = cultivo_actual["id"]
            if cid is None:
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                cultivo = session.get(Cultivo, cid)
                if cultivo is None:
                    return
                nome = nome_cultivo(cultivo)
                resumo = resumo_estimacion(session, actor, cid)
                estimacions = listar_estimacions(session, actor, cid)

            titulo.text = f"Estimación da colleita — {nome}"

            with ui.card().classes("w-full p-3 bg-slate-50 border"):
                ui.label("Resumo").classes("text-subtitle2 font-bold")
                with ui.row().classes("w-full gap-4 text-body2"):
                    obj_txt = (
                        f"{formatar_enteiro(resumo.obxectivo_kg_ha)} kg/ha"
                        if resumo.obxectivo_kg_ha is not None
                        else "—"
                    )
                    est_txt = (
                        f"{formatar_enteiro(resumo.estimado_kg_ha)} kg/ha"
                        if resumo.estimado_kg_ha is not None
                        else "—"
                    )
                    tot_txt = (
                        f"{formatar_enteiro(resumo.estimado_total_kg)} kg"
                        if resumo.estimado_total_kg is not None
                        else "—"
                    )
                    col_txt = (
                        f"{formatar_enteiro(resumo.colleitado_kg_ha)} kg/ha"
                        if resumo.colleitado_kg_ha is not None
                        else "—"
                    )
                    pct_txt = (
                        f"{formatar_enteiro(resumo.porcentaxe_colleitada)} %"
                        if resumo.porcentaxe_colleitada is not None
                        else "—"
                    )
                    with ui.column().classes("gap-0"):
                        ui.label("Obxectivo").classes("text-caption text-grey-7")
                        ui.label(obj_txt).classes("font-semibold")
                    with ui.column().classes("gap-0"):
                        ui.label("Estimado").classes("text-caption text-grey-7")
                        ui.label(est_txt).classes("font-semibold")
                    with ui.column().classes("gap-0"):
                        ui.label("Total estimado").classes("text-caption text-grey-7")
                        ui.label(tot_txt).classes("font-semibold")
                    with ui.column().classes("gap-0"):
                        ui.label("Colleitado").classes("text-caption text-grey-7")
                        ui.label(col_txt).classes("font-semibold")
                    with ui.column().classes("gap-0"):
                        ui.label("% colleitada").classes("text-caption text-grey-7")
                        ui.label(pct_txt).classes("font-semibold")

            ui.label("Estimacións").classes("text-subtitle2 font-bold")
            if not estimacions:
                ui.label("Aínda non hai estimacións.").classes("text-body2 text-grey-7")
            else:
                with ui.column().classes("w-full gap-2"):
                    for e in estimacions:
                        with ui.card().classes("w-full p-2 border"):
                            with ui.row().classes("w-full items-center justify-between"):
                                with ui.column().classes("gap-0"):
                                    with ui.row().classes("items-center gap-2"):
                                        ui.label(f"{e.data:%d/%m/%Y}").classes("font-bold")
                                        met_nome = (
                                            "Mostraxe" if e.metodo == "mostraxe" else "Directa"
                                        )
                                        ui.label(met_nome).classes("text-caption text-grey-7")
                                        ui.label(
                                            f"{formatar_enteiro(e.kg_ha)} kg/ha"
                                        ).classes("font-semibold text-primary")
                                    if e.metodo == "mostraxe" and e.plantas_ha:
                                        p_txt = formatar_decimal(e.plantas_ha)
                                        u_txt = formatar_decimal(e.unidades_planta)
                                        w_txt = formatar_decimal(e.peso_unidade_g)
                                        ui.label(
                                            f"{p_txt} pl/ha × {u_txt} pezas/pl × {w_txt} g"
                                        ).classes("text-caption text-grey-7")
                                    if e.notas:
                                        ui.label(e.notas).classes("text-caption text-grey-8")
                                if pode_editar:
                                    def facer_borrado(eid: int = e.id) -> None:
                                        def confirmar() -> None:
                                            with get_session() as sess:
                                                act = usuario_actual(sess)
                                                if act is None:
                                                    return
                                                ok = executar_accion(
                                                    sess,
                                                    lambda: borrar_estimacion(sess, act, eid),
                                                )
                                            if ok:
                                                contido_dialogo.refresh()

                                        confirmar_eliminacion(
                                            "Borrar esta estimación?", confirmar
                                        )

                                    ui.button(
                                        icon="delete", on_click=facer_borrado
                                    ).props("flat dense color=negative")

            if pode_editar:
                ui.separator()
                ui.label("Nova estimación").classes("text-subtitle2 font-bold")
                data_in = campo_data("Data", date.today().isoformat())
                metodo_in = ui.select(
                    {"mostraxe": "Mostraxe no campo", "directa": "Directa"},
                    value="mostraxe",
                    label="Método",
                ).classes("w-full")

                mostraxe_col = ui.column().classes("w-full gap-2")
                with mostraxe_col:
                    ui.label(
                        "Conta as plantas por hectárea, os froitos ou pezas por planta "
                        "nunhas cantas plantas e o peso medio dunha peza"
                    ).classes("text-caption text-grey-7")
                    with ui.row().classes("w-full gap-2"):
                        plantas_in = ui.input("Plantas/ha").classes("col-grow")
                        unidades_in = ui.input("Pezas/planta").classes("col-grow")
                        peso_in = ui.input("Peso medio peza (g)").classes("col-grow")
                    calc_lbl = ui.label("").classes("text-sm font-semibold text-primary")

                    def calcular_mostraxe() -> None:
                        try:
                            p = parsear_decimal(plantas_in.value)
                            u = parsear_decimal(unidades_in.value)
                            w = parsear_decimal(peso_in.value)
                            if p and u and w and p > 0 and u > 0 and w > 0:
                                kg = kg_ha_por_mostraxe(p, u, w)
                                calc_lbl.text = f"Cálculo: {formatar_enteiro(kg)} kg/ha"
                            else:
                                calc_lbl.text = ""
                        except Exception:
                            calc_lbl.text = ""

                    plantas_in.on_value_change(calcular_mostraxe)
                    unidades_in.on_value_change(calcular_mostraxe)
                    peso_in.on_value_change(calcular_mostraxe)

                directa_col = ui.column().classes("w-full gap-2")
                with directa_col:
                    kg_ha_in = ui.input("Estimación (kg/ha)").classes("w-full")

                directa_col.set_visibility(False)

                def alternar_metodo() -> None:
                    e_mostraxe = metodo_in.value == "mostraxe"
                    mostraxe_col.set_visibility(e_mostraxe)
                    directa_col.set_visibility(not e_mostraxe)

                metodo_in.on_value_change(alternar_metodo)

                notas_in = ui.textarea("Notas").classes("w-full")

                def gardar_nova() -> None:
                    cid = cultivo_actual["id"]
                    if cid is None:
                        return
                    with get_session() as session:
                        actor = usuario_actual(session)
                        if actor is None:
                            pechar_sesion()
                            return

                        def accion() -> None:
                            dt = parsear_data(data_in.value) or date.today()
                            met = metodo_in.value or "mostraxe"
                            p = parsear_decimal(plantas_in.value)
                            u = parsear_decimal(unidades_in.value)
                            w = parsear_decimal(peso_in.value)
                            k = parsear_decimal(kg_ha_in.value)
                            crear_estimacion(
                                session,
                                actor,
                                cultivo_id=cid,
                                data=dt,
                                metodo=met,
                                kg_ha=k,
                                plantas_ha=p,
                                unidades_planta=u,
                                peso_unidade_g=w,
                                notas=notas_in.value or None,
                            )

                        ok = executar_accion(session, accion)
                    if ok:
                        contido_dialogo.refresh()

                with ui.row():
                    ui.button("Gardar estimación", icon="check", on_click=gardar_nova)

        contido_dialogo()

    def abrir(cid: int) -> None:
        cultivo_actual["id"] = cid
        contido_dialogo.refresh()
        dialogo.open()

    return abrir
