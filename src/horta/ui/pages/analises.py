"""Sección Análises: de cultivo, produto colleitado, solo ou auga (CUE bloque 13)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.analise import Analise
from horta.models.parcela import Parcela
from horta.services.analises import (
    SOLO,
    DatosAnalise,
    actualizar_analise,
    crear_analise,
    dar_de_baixa_analise,
    listar_analises,
)
from horta.services.catalogos import valores_vixentes
from horta.services.colleitas import listar_colleitas
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

RESIDUOS = "1"  # catálogo TIPO_ANALISIS
_PARAMETROS_SOLO = (("materia_organica", "Materia orgánica (%)"), ("ph", "pH"),
                    ("area", "Area (%)"), ("limo", "Limo (%)"), ("arxila", "Arxila (%)"),
                    ("n_total", "Nitróxeno total (%)"), ("fosforo_ppm", "Fósforo (ppm)"),
                    ("potasio_ppm", "Potasio (ppm)"),
                    ("conductividade", "Condutividade (dS/m)"),
                    ("cadmio", "Cadmio (mg/kg)"), ("cobre", "Cobre (mg/kg)"),
                    ("niquel", "Níquel (mg/kg)"), ("chumbo", "Chumbo (mg/kg)"),
                    ("zinc", "Cinc (mg/kg)"), ("mercurio", "Mercurio (mg/kg)"),
                    ("cromo", "Cromo total (mg/kg)"))


def seccion_analises(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        analises = listar_analises(session, actor, horta_id)
        _ = [(a.tipos, a.substancias) for a in analises]
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}

    def onde(a: Analise) -> str:
        return ", ".join(x for x in (parcelas.get(a.parcela_id or 0),
                                      cultivos.get(a.cultivo_id or 0),
                                      lotes.get(a.colleita_id or 0)) if x)

    filas = [{
        "id": a.id,
        "data": f"{a.data_mostraxe:%d/%m/%Y}",
        "material": materiais.get(a.material_analizado, a.material_analizado),
        "onde": onde(a),
        "tipos": ", ".join(tipos.get(t.codigo, t.codigo) for t in a.tipos),
        "laboratorio": a.laboratorio or "",
    } for a in analises]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("material", "Que"), ("onde", "Onde"), ("tipos", "Análise"),
            ("laboratorio", "Laboratorio"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai análises" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_analise(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        abrir(next(a for a in analises if a.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro unha análise na táboa", type="warning")
            return
        analise_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Analise, analise_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_analise(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta análise? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar análise", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_analise(horta_id: int) -> Callable[[Analise | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha análise e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
        substancias = {v.codigo: v.descricion
                       for v in valores_vixentes(session, "substancia_activa")}

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar análise").classes("text-h6")
        if not materiais:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
        material = ui.select(materiais, label="Que se analizou").classes("w-full")
        data = campo_data("Data da mostra", date.today().isoformat())
        tipo = ui.select(tipos, multiple=True, label="Tipo de análise").classes(
            "w-full").props("use-chips")
        parcela = ui.select(parcelas, label="Parcela", clearable=True).classes("w-full")
        cultivo = ui.select(cultivos, label="Cultivo", clearable=True).classes("w-full")
        lote = ui.select(lotes, label="Lote da colleita", clearable=True,
                         with_input=True).classes("w-full")
        substancia = ui.select(substancias, multiple=True, with_input=True,
                               label="Substancias activas detectadas").classes(
            "w-full").props("use-chips")
        substancia.bind_visibility_from(tipo, "value",
                                        backward=lambda v: RESIDUOS in (v or []))
        with ui.expansion("Resultados do solo").classes("w-full") as solo:
            parametros = {campo: ui.input(etiqueta).classes("w-full")
                          for campo, etiqueta in _PARAMETROS_SOLO}
        solo.bind_visibility_from(material, "value", backward=lambda v: v == SOLO)
        with ui.expansion("Laboratorio e notas").classes("w-full"):
            laboratorio = ui.input("Laboratorio").classes("w-full")
            nif = ui.input("NIF do laboratorio").classes("w-full")
            boletin = ui.input("Nº de boletín").classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def gardar() -> None:
            if material.value is None:
                ui.notify("Escolle que se analizou", type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    mostra = parsear_data(data.value)
                    if mostra is None:
                        raise OperacionNonPermitidaError("Indica a data da mostra")
                    datos = DatosAnalise(
                        material_analizado=material.value, data_mostraxe=mostra,
                        tipos=list(tipo.value or []),
                        substancias=list(substancia.value or [])
                        if RESIDUOS in (tipo.value or []) else [],
                        laboratorio=laboratorio.value or None,
                        laboratorio_nif=nif.value or None, num_boletin=boletin.value or None,
                        parcela_id=parcela.value, cultivo_id=cultivo.value,
                        colleita_id=lote.value,
                        solo={c: parsear_decimal(i.value) for c, i in parametros.items()}
                        if material.value == SOLO else {},
                        notas=notas.value or None)
                    existente = session.get(Analise, editando["id"]) if editando["id"] else None
                    if existente is None:
                        crear_analise(session, actor_actual, horta_id, datos)
                    else:
                        actualizar_analise(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(a: Analise | None) -> None:
        editando["id"] = a.id if a else None
        titulo.text = "Editar análise" if a else "Apuntar análise"
        material.value = a.material_analizado if a else None
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
        tipo.value = [t.codigo for t in a.tipos] if a else []
        substancia.value = [s.codigo for s in a.substancias] if a else []
        parcela.value = a.parcela_id if a else None
        cultivo.value = a.cultivo_id if a else None
        lote.value = a.colleita_id if a else None
        for campo, entrada in parametros.items():
            valor = getattr(a, campo) if a else None
            entrada.value = "" if valor is None else f"{valor:g}"
        laboratorio.value = (a.laboratorio or "") if a else ""
        nif.value = (a.laboratorio_nif or "") if a else ""
        boletin.value = (a.num_boletin or "") if a else ""
        notas.value = (a.notas or "") if a else ""
        dialogo.open()

    return abrir
