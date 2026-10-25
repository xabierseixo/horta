"""Sección Labores: cada labor cultural dun cultivo (CUE bloque 5). Baixa lóxica."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.labor import Labor
from horta.models.parcela import Parcela
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.labores import (
    DESBROCE,
    PODAS,
    DatosLabor,
    actualizar_labor,
    crear_labor,
    dar_de_baixa_labor,
    listar_labores,
    ultimo_labor,
)
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA


def seccion_labores(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        labores = listar_labores(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_labor")}
        coberturas = {v.codigo: v.descricion
                      for v in valores_vixentes(session, "tipo_cobertura_solo")}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    filas = [{
        "id": lab.id,
        "data": f"{lab.data_inicio:%d/%m/%Y}",
        "cultivo": cultivos.get(lab.cultivo_id, ""),
        "labor": tipos.get(lab.tipo_labor, lab.tipo_labor),
        "maquina": maquinas.get(lab.maquina_id, "") if lab.maquina_id else "",
    } for lab in labores]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("labor", "Labor"),
            ("maquina", "Máquina"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai labores" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    if not tipos:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar labor").classes("text-h6")
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        tipo = ui.select(tipos, label="Labor").classes("w-full")
        restos_desbroce = ui.checkbox("Os restos do desbroce quedaron no chan")
        restos_poda = ui.checkbox("Os restos da poda quedaron no chan")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            superficie = CampoSuperficie("Superficie (baleiro = a do cultivo)")
            cobertura = ui.select(coberturas, label="Cobertura do solo (baleiro = a do cultivo)",
                                  clearable=True).classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                repeticions = ui.input("Nº de pasadas").classes("col")
                horas = ui.input("Horas de cada pasada").classes("col")
            persoa = ui.select(persoas, label="Quen o fixo", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def mostrar_restos() -> None:
            restos_desbroce.set_visibility(tipo.value == DESBROCE)
            restos_poda.set_visibility(tipo.value in PODAS)

        tipo.on_value_change(mostrar_restos)

        def propor_labor() -> None:
            if cultivo.value is not None and tipo.value is None:
                with get_session() as session:
                    tipo.value = ultimo_labor(session, cultivo.value)

        cultivo.on_value_change(propor_labor)

        def gardar() -> None:
            if cultivo.value is None or tipo.value is None:
                ui.notify("Escolle o cultivo e o labor", type="warning")
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
                    pasadas = parsear_decimal(repeticions.value)
                    datos = DatosLabor(
                        cultivo_id=cultivo.value, data_inicio=inicio, tipo_labor=tipo.value,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
                        restos_desbroce_no_solo=bool(restos_desbroce.value),
                        restos_poda_no_solo=bool(restos_poda.value),
                        tipo_cobertura=cobertura.value, maquina_id=maquina.value,
                        num_repeticions=int(pasadas) if pasadas is not None else None,
                        duracion_h=parsear_decimal(horas.value), persoa_id=persoa.value,
                        notas=notas.value or None)
                    existente = session.get(Labor, editando["id"]) if editando["id"] else None
                    if existente is None:
                        crear_labor(session, actor_actual, datos)
                    else:
                        actualizar_labor(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(lab: Labor | None) -> None:
        editando["id"] = lab.id if lab else None
        titulo.text = "Editar labor" if lab else "Apuntar labor"
        tipo.value = lab.tipo_labor if lab else None
        cultivo.value = lab.cultivo_id if lab else None
        data_inicio.value = (lab.data_inicio if lab else date.today()).isoformat()
        data_fin.value = (lab.data_fin.isoformat()
                          if lab and lab.data_fin != lab.data_inicio else "")
        superficie.establecer(lab.superficie_ha if lab else None)
        restos_desbroce.value = bool(lab and lab.restos_desbroce_no_solo)
        restos_poda.value = bool(lab and lab.restos_poda_no_solo)
        cobertura.value = lab.tipo_cobertura if lab else None
        maquina.value = lab.maquina_id if lab and lab.maquina_id in maquinas else None
        repeticions.value = str(lab.num_repeticions) if lab and lab.num_repeticions else ""
        horas.value = f"{lab.duracion_h:g}" if lab and lab.duracion_h else ""
        persoa.value = lab.persoa_id if lab and lab.persoa_id in persoas else None
        notas.value = (lab.notas or "") if lab else ""
        mostrar_restos()
        dialogo.open()

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        with get_session() as session:
            lab = session.get(Labor, taboa.selected[0]["id"])
            if lab is not None:
                abrir(lab)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un labor na táboa", type="warning")
            return
        labor_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                lab = session.get(Labor, labor_id)
                if actor_actual is None or lab is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_labor(
                    session, actor_actual, lab))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este labor? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar labor", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")
