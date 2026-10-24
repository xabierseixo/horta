"""Sección Colleitas: cada colleita co seu lote. Baixa lóxica, como os tratamentos."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.colleita import Colleita
from horta.services.catalogos import valores_vixentes
from horta.services.colleitas import (
    UNIDADES_COLLEITA,
    DatosColleita,
    actualizar_colleita,
    crear_colleita,
    dar_de_baixa_colleita,
    listar_colleitas,
    propor_lote,
    rendemento_kg_ha,
)
from horta.services.cultivos import listar_cultivos
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie


def seccion_colleitas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        colleitas = listar_colleitas(session, actor, horta_id)
        cultivos = listar_cultivos(session, actor, horta_id)
        destinos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_colleita")}
        restos = {v.codigo: v.descricion for v in valores_vixentes(session, "destino_restos")}
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
            ("lote", "Lote"), ("destino", "Destino"))],
        rows=filas, row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai colleitas"'
    )

    if not pode_editar:
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("Apuntar colleita").classes("text-h6")
        cultivo = ui.select(nome_cultivo, label="Cultivo", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
        lote = ui.input("Lote").classes("w-full")
        albaran = ui.input("Nº de albarán ou factura (opcional)").classes("w-full")
        superficie = CampoSuperficie("Superficie colleitada (baleiro = a do cultivo)")
        data_fin = campo_data("Data de fin (se durou máis dun día)")
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
            if editando["id"] is not None or cultivo.value is None:
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    return
                lote.value = propor_lote(session, actor, cultivo.value,
                                         parsear_data(data.value) or date.today())

        cultivo.on_value_change(propor)

        def gardar() -> None:
            if cultivo.value is None:
                ui.notify("Escolle o cultivo", type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    datos = DatosColleita(
                        cultivo_id=cultivo.value,
                        data=parsear_data(data.value) or date.today(),
                        cantidade=parsear_decimal(cantidade.value) or 0,
                        unidade=unidade.value,
                        lote=lote.value or "",
                        superficie_ha=superficie.ha,
                        destino_colleita=destino.value,
                        destino_restos=destino_restos.value,
                        notas=notas.value or None,
                        data_fin=parsear_data(data_fin.value),
                        albaran_factura=albaran.value or None,
                        obten_sementes=sementes.value,
                        obten_plantas=plantas.value,
                        sen_colleita_ambiental=sen_colleita.value,
                        restos_no_solo=restos_solo.value,
                    )
                    if editando["id"] is None:
                        crear_colleita(session, actor, datos)
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

    def abrir_nova() -> None:
        editando["id"] = None
        titulo.text = "Apuntar colleita"
        cultivo.value = None
        data.value = date.today().isoformat()
        for campo in (cantidade, lote, notas, data_fin, albaran):
            campo.value = ""
        superficie.establecer(None)
        sementes.value = plantas.value = sen_colleita.value = restos_solo.value = False
        unidade.value = "kg"
        destino.value = destino_restos.value = None
        dialogo.open()

    def abrir_edicion() -> None:
        if not taboa.selected:
            ui.notify("Selecciona unha colleita na táboa", type="warning")
            return
        c = next(x for x in colleitas if x.id == taboa.selected[0]["id"])
        editando["id"] = c.id
        titulo.text = "Editar colleita"
        cultivo.value = c.cultivo_id
        data.value = c.data.isoformat()
        cantidade.value = f"{c.cantidade:g}"
        unidade.value = c.unidade
        lote.value = c.lote
        superficie.establecer(c.superficie_ha)
        destino.value = c.destino_colleita
        destino_restos.value = c.destino_restos
        notas.value = c.notas or ""
        data_fin.value = c.data_fin.isoformat() if c.data_fin else ""
        albaran.value = c.albaran_factura or ""
        sementes.value = c.obten_sementes
        plantas.value = c.obten_plantas
        sen_colleita.value = c.sen_colleita_ambiental
        restos_solo.value = c.restos_no_solo
        dialogo.open()

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
        ui.button("Apuntar colleita", icon="add", on_click=abrir_nova)
        ui.button("Editar", icon="edit", on_click=abrir_edicion).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")
