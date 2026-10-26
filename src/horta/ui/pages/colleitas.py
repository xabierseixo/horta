"""Sección Colleitas: cada colleita co seu lote. Baixa lóxica, como os tratamentos."""

from __future__ import annotations

from collections.abc import Callable
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
from horta.services.fito_consulta import aviso_prazo_colleita
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
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
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
    )

    if not pode_editar:
        return

    abrir = dialogo_colleita(horta_id)

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
        with ui.expansion("Cliente (se se vende a unha empresa)").classes("w-full"):
            cliente_nome = ui.input("Nome ou razón social").classes("w-full")
            cliente_nif = ui.input("NIF").classes("w-full")
            cliente_enderezo = ui.input("Enderezo").classes("w-full")
            cliente_reaga = ui.input("Nº REAGA (se é unha explotación)").classes("w-full")
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
        aviso_prazo = ui.label().classes("text-negative text-sm")

        def comprobar_prazo() -> None:
            dia = parsear_data(data.value) if data.value else None
            if cultivo.value is None or dia is None:
                aviso_prazo.text = ""
                return
            with get_session() as session:
                aviso_prazo.text = aviso_prazo_colleita(session, cultivo.value, dia) or ""

        cultivo.on_value_change(comprobar_prazo)
        data.on_value_change(comprobar_prazo)

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
                        cliente_nome=cliente_nome.value or None,
                        cliente_nif=cliente_nif.value or None,
                        cliente_enderezo=cliente_enderezo.value or None,
                        cliente_reaga=cliente_reaga.value or None,
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

    def abrir(c: Colleita | None) -> None:
        editando["id"] = c.id if c else None
        titulo.text = "Editar colleita" if c else "Apuntar colleita"
        cultivo.value = c.cultivo_id if c else None
        data.value = (c.data if c else date.today()).isoformat()
        cantidade.value = f"{c.cantidade:g}" if c else ""
        unidade.value = c.unidade if c else "kg"
        lote.value = c.lote if c else ""
        superficie.establecer(c.superficie_ha if c else None)
        destino.value = c.destino_colleita if c else None
        destino_restos.value = c.destino_restos if c else None
        notas.value = (c.notas or "") if c else ""
        data_fin.value = c.data_fin.isoformat() if c and c.data_fin else ""
        albaran.value = (c.albaran_factura or "") if c else ""
        cliente_nome.value = (c.cliente_nome or "") if c else ""
        cliente_nif.value = (c.cliente_nif or "") if c else ""
        cliente_enderezo.value = (c.cliente_enderezo or "") if c else ""
        cliente_reaga.value = (c.cliente_reaga or "") if c else ""
        sementes.value = bool(c and c.obten_sementes)
        plantas.value = bool(c and c.obten_plantas)
        sen_colleita.value = bool(c and c.sen_colleita_ambiental)
        restos_solo.value = bool(c and c.restos_no_solo)
        dialogo.open()

    return abrir
