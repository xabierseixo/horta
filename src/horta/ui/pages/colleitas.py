"""Sección Colleitas: cada colleita co seu lote. Baixa lóxica, como os tratamentos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.colleita import Colleita
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
from horta.services.cultivos import listar_cultivos
from horta.services.fito_consulta import aviso_prazo_colleita
from horta.services.lotes import listar_lotes, resumo_lotes
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
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
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
        con_colleitas = {c.cultivo_id for c in colleitas}
        rendementos = {c.id: rendemento_kg_ha(session, actor, c.id)
                       for c in cultivos if c.id in con_colleitas}

    nome_cultivo = {c.id: f"{c.especie} {c.variedade or ''}".strip() for c in cultivos}
    filas = [
        {
            "id": c.id,
            "data": f"{c.data:%d/%m/%Y}",
            "cultivo": nome_cultivo.get(c.cultivo_id, ""),
            "cantidade": f"{c.cantidade:g} {c.unidade}",
            "lote": c.lote,
        "queda": (f"{queda[c.lote_id][2]:g} {unidades_lote[c.lote_id]}"
                  if c.lote_id in queda else ""),
            "destino": destinos.get(c.destino_colleita or "", ""),
        }
        for c in colleitas
    ]
    with ui.row().classes("gap-4"):
        for cultivo_id, kg_ha in rendementos.items():
            if kg_ha is not None:
                ui.label(f"{nome_cultivo[cultivo_id]}: {kg_ha:.0f} kg/ha").classes("text-body2")
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("cantidade", "Cantidade"),
            ("lote", "Lote"), ("queda", "Queda"), ("destino", "Destino"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
    )

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

    with ui.row():
        ui.button("Apuntar colleita", icon="add", on_click=lambda: abrir(None))
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
        nome_cultivo = {c.id: f"{c.especie} {c.variedade or ''}".strip()
                        for c in listar_cultivos(session, actor, horta_id)}
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("Apuntar colleita").classes("text-h6")
        # Varias leiras dunha vez: unha colleita por leira, coa súa cantidade e no mesmo lote
        cultivo = ui.select(nome_cultivo, label="Leiras (unha ou varias)", with_input=True,
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
                    cantidades[cultivo_id] = ui.input(nome_cultivo.get(cultivo_id, "")).classes(
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
                ui.navigate.reload()

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
