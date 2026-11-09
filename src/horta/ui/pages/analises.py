"""Sección Análises: de cultivo, produto colleitado, solo ou auga (CUE bloque 13)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.analise import Analise
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
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
from horta.services.persoas import listar_persoas, listar_quen
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

RESIDUOS = "1"  # catálogo TIPO_ANALISIS
_PARAMETROS_SOLO = (("materia_organica", N_("Materia orgánica (%)")), ("ph", N_("pH")),
                    ("area", N_("Area (%)")), ("limo", N_("Limo (%)")),
                    ("arxila", N_("Arxila (%)")),
                    ("n_total", N_("Nitróxeno total (%)")),
                    ("fosforo_ppm", N_("Fósforo (ppm)")),
                    ("potasio_ppm", N_("Potasio (ppm)")),
                    ("conductividade", N_("Condutividade (dS/m)")),
                    ("cadmio", N_("Cadmio (mg/kg)")), ("cobre", N_("Cobre (mg/kg)")),
                    ("niquel", N_("Níquel (mg/kg)")), ("chumbo", N_("Chumbo (mg/kg)")),
                    ("zinc", N_("Cinc (mg/kg)")), ("mercurio", N_("Mercurio (mg/kg)")),
                    ("cromo", N_("Cromo total (mg/kg)")))


def seccion_analises(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        analises = listar_analises(session, actor, horta_id)
        _x = [(a.tipos, a.substancias) for a in analises]
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                 for v in valores_vixentes(session, "tipo_analise")}
        nomes = {p.id: p.nome
                 for p in listar_persoas(session, actor, horta_id, so_activas=False)}

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
        "laboratorio": nomes.get(a.laboratorio_id or 0, ""),
    } for a in analises]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", _("Data")), ("material", _("Que")), ("onde", _("Onde")),
            ("tipos", _("Análise")), ("laboratorio", _("Laboratorio")))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="{_("Aínda non hai análises")}" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "data", ["material", "tipos"], accions_tarxeta)

    if not pode_editar:
        return
    abrir = dialogo_analise(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify(_("Escolle primeiro unha análise na táboa"), type="warning")
            return
        abrir(next(a for a in analises if a.id == taboa.selected[0]["id"]))

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify(_("Escolle primeiro unha análise na táboa"), type="warning")
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
            _("Dar de baixa esta análise? Non se borra: consérvase no histórico."), confirmar)

    accions_tarxeta += [(_("Editar"), "edit", editar),
                        (_("Dar de baixa"), "archive", dar_de_baixa)]

    with ui.row():
        ui.button(_("Apuntar análise"), icon="add", on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador"):
            ui.button(_("Editar"), icon="edit", on_click=editar).props("outline")
            ui.button(_("Dar de baixa"), icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_analise(horta_id: int) -> Callable[[Analise | None], None]:
    """Constrúe o diálogo de apuntar ou editar unha análise e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _x: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                 for v in valores_vixentes(session, "tipo_analise")}
        substancias = {v.codigo: v.descricion
                       for v in valores_vixentes(session, "substancia_activa")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label(_("Apuntar análise")).classes("text-h6")
        if not materiais:
            ui.label(_(AVISO_SEN_CATALOGOS)).classes("text-warning text-caption")
        material = ui.select(materiais, label=_("Que se analizou")).classes("w-full")
        data = campo_data(_("Data da mostra"), date.today().isoformat())
        persoa = ui.select(persoas, label=_("Quen colleu a mostra")).classes("w-full")
        tipo = ui.select(tipos, multiple=True, label=_("Tipo de análise")).classes(
            "w-full").props("use-chips")
        parcela = ui.select(parcelas, label=_("Parcela"), clearable=True).classes("w-full")
        cultivo = ui.select(cultivos, label=_("Cultivo"), clearable=True).classes("w-full")
        lote = ui.select(lotes, label=_("Lote da colleita"), clearable=True,
                         with_input=True).classes("w-full")
        substancia = ui.select(substancias, multiple=True, with_input=True,
                               label=_("Substancias activas detectadas")).classes(
            "w-full").props("use-chips")
        substancia.bind_visibility_from(tipo, "value",
                                        backward=lambda v: RESIDUOS in (v or []))
        with ui.expansion(_("Resultados do solo")).classes("w-full") as solo:
            parametros = {campo: ui.input(_(etiqueta)).classes("w-full")
                          for campo, etiqueta in _PARAMETROS_SOLO}
        solo.bind_visibility_from(material, "value", backward=lambda v: v == SOLO)
        with ui.expansion(_("Laboratorio e notas")).classes("w-full"):
            laboratorio = CampoPersoa(horta_id, "laboratorio", _("Laboratorio"))
            boletin = ui.input(_("Nº de boletín")).classes("w-full")
            horas = ui.input(_("Horas de traballo")).classes("w-full")
            notas = ui.textarea(_("Notas")).classes("w-full")

        def gardar() -> None:
            if material.value is None:
                ui.notify(_("Escolle que se analizou"), type="warning")
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    mostra = parsear_data(data.value)
                    if mostra is None:
                        raise OperacionNonPermitidaError(_("Indica a data da mostra"))
                    datos = DatosAnalise(
                        material_analizado=material.value, data_mostraxe=mostra,
                        tipos=list(tipo.value or []),
                        substancias=list(substancia.value or [])
                        if RESIDUOS in (tipo.value or []) else [],
                        laboratorio_id=laboratorio.value, num_boletin=boletin.value or None,
                        parcela_id=parcela.value, cultivo_id=cultivo.value,
                        colleita_id=lote.value,
                        solo={c: parsear_decimal(i.value) for c, i in parametros.items()}
                        if material.value == SOLO else {},
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        notas=notas.value or None)
                    existente = session.get(Analise, editando["id"]) if editando["id"] else None
                    if existente is None:
                        novo = crear_analise(session, actor_actual, horta_id, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_analise(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("analise", data.value)

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    def abrir(a: Analise | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = a.id if a else None
        titulo.text = _("Editar análise") if a else _("Apuntar análise")
        material.value = a.material_analizado if a else None
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
        persoa.value = (a.persoa_id if a.persoa_id in persoas else None) if a else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{a.horas:g}" if a and a.horas else ""
        tipo.value = [t.codigo for t in a.tipos] if a else []
        substancia.value = [s.codigo for s in a.substancias] if a else []
        parcela.value = a.parcela_id if a else (tarefa.parcela_id if tarefa else None)
        cultivo.value = a.cultivo_id if a else (tarefa.cultivo_id if tarefa else None)
        lote.value = a.colleita_id if a else None
        for campo, entrada in parametros.items():
            valor = getattr(a, campo) if a else None
            entrada.value = "" if valor is None else f"{valor:g}"
        laboratorio.value = a.laboratorio_id if a else None
        boletin.value = (a.num_boletin or "") if a else ""
        notas.value = (a.notas or "") if a else ""
        dialogo.open()

    return abrir
