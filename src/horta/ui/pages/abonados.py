"""Sección Fertilización: cada abonado dun cultivo (CUE bloque 9). Baixa lóxica."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.abonado import Abonado, Fertilizante
from horta.models.parcela import Parcela
from horta.services.abonados import (
    DatosAbonado,
    actualizar_abonado,
    crear_abonado,
    dar_de_baixa_abonado,
    listar_abonados,
    nutrientes_do_abonado,
)
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, listar_fertilizantes, nutrientes_kg_ha
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.services.plan_abonado import balance_do_cultivo
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.dialogo_abono import dialogo_novo_abono
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA


def _nutrientes(npk: tuple[float, float, float] | None) -> str:
    return "" if npk is None else f"N {npk[0]:g} · P₂O₅ {npk[1]:g} · K₂O {npk[2]:g} kg/ha"


def seccion_abonados(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        abonados = listar_abonados(session, actor, horta_id)
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        lista_cultivos = listar_cultivos(session, actor, horta_id)
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in lista_cultivos}
        abonados_cultivos = {a.cultivo_id for a in abonados}
        balances = {c.id: balance_do_cultivo(session, actor, horta_id, c) for c in lista_cultivos
                    if c.id in abonados_cultivos or c.plan_necesidade_n}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        filas = [{
            "id": a.id,
            "data": f"{a.data_inicio:%d/%m/%Y}",
            "cultivo": cultivos.get(a.cultivo_id, ""),
            "abono": abonos.get(a.fertilizante_id or 0, "abonado en verde"),
            "dose": f"{a.dose:g} {unidades.get(a.unidade or '', '')}" if a.dose else "",
            "nutrientes": _nutrientes(nutrientes_do_abonado(session, a)),
        } for a in abonados]

    for cultivo_id, balance in balances.items():
        partes = []
        for nome, feito, preciso in zip(("N", "P₂O₅", "K₂O"), balance.aplicado,
                                        balance.necesidade):
            if feito or preciso:
                partes.append(f"{nome} {feito:g}" + (f" de {preciso:g}" if preciso else ""))
        aviso = (f" (sen contar {balance.sen_calcular}: falta a densidade)"
                 if balance.sen_calcular else "")
        ui.label(f"{cultivos[cultivo_id]}: {' · '.join(partes) or 'nada'} kg/ha{aviso}").classes(
            "text-body2")
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("cultivo", "Cultivo"), ("abono", "Abono"), ("dose", "Dose"),
            ("nutrientes", "Achega"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai abonados" {TEXTOS_TABOA}')

    if not pode_editar:
        return
    abrir = dialogo_abonado(horta_id)

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        with get_session() as session:
            a = session.get(Abonado, taboa.selected[0]["id"])
            if a is not None:
                _ = a.boas_practicas
                abrir(a)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un abonado na táboa", type="warning")
            return
        abonado_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                a = session.get(Abonado, abonado_id)
                if actor_actual is None or a is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_abonado(
                    session, actor_actual, a))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este abonado? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Apuntar abonado", icon="add", on_click=lambda: abrir(None))
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_abonado(horta_id: int) -> Callable[[Abonado | None], None]:
    """Constrúe o diálogo de apuntar ou editar un abonado e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _: None
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} {c.variedade or ''} — {parcelas[c.parcela_id]}".strip()
                    for c in listar_cultivos(session, actor, horta_id)}
        abonos = {f.id: f.nome for f in listar_fertilizantes(session, actor, horta_id)}
        unidades_cat = {v.codigo: v.descricion for v in valores_vixentes(session, "unidade_medida")}
        unidades = {c: unidades_cat[c] for c in UNIDADES_DOSE if c in unidades_cat}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_fertilizacion")}
        metodos = {v.codigo: v.descricion
                   for v in valores_vixentes(session, "metodo_fertilizacion")}
        practicas = {v.codigo: v.descricion for v in valores_vixentes(session, "boas_practicas")
                     if "fertilizacion" in (v.categoria or "")}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None}

    def abono_creado(abono_id: int, nome: str) -> None:
        abonos[abono_id] = nome
        abono.set_options(abonos, value=abono_id)

    novo_abono = dialogo_novo_abono(horta_id, abono_creado)

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar abonado").classes("text-h6")
        if not tipos or not practicas:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
        cultivo = ui.select(cultivos, label="Cultivo", with_input=True).classes("w-full")
        data_inicio = campo_data("Data", date.today().isoformat())
        aplicador = ui.select(persoas, label="Quen o botou", clearable=True).classes("w-full")
        superficie = CampoSuperficie("Superficie abonada (baleiro = a do cultivo)")
        with ui.row().classes("w-full no-wrap items-center"):
            abono = ui.select(abonos, label="Abono", with_input=True).classes("col")
            ui.button(icon="add", on_click=novo_abono.open).props(
                'flat round aria-label="Novo abono"')
        with ui.row().classes("w-full no-wrap"):
            dose = ui.input("Dose").classes("col")
            unidade = ui.select(unidades, value="17", label="Unidade").classes("col")
        achega = ui.label().classes("text-caption")
        tipo = ui.select(tipos, label="Tipo de abonado").classes("w-full")
        metodo = ui.select(metodos, label="Como se botou").classes("w-full")
        boas = ui.select(practicas, multiple=True, label="Boas prácticas").classes(
            "w-full").props("use-chips")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
            xestion = ui.checkbox("Xestión sostible dos insumos")
            lodos = ui.checkbox("Leva documento de aplicación de lodos de depuradora")
            albaran = ui.input("Albará ou factura").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            empresa = ui.input("REGFER da empresa de servizos (se o fixo unha)").classes(
                "w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def calcular() -> None:
            valor = parsear_decimal(dose.value)
            if abono.value is None or not valor or unidade.value is None:
                achega.text = ""
                return
            with get_session() as session:
                fertilizante = session.get(Fertilizante, abono.value)
                npk = nutrientes_kg_ha(fertilizante, valor, unidade.value) if fertilizante \
                    else None
            achega.text = ("= " + _nutrientes(npk)) if npk else \
                "Non se pode calcular a achega (falta a densidade do líquido)"

        for campo in (abono, dose, unidade):
            campo.on_value_change(calcular)

        def gardar() -> None:
            if cultivo.value is None:
                ui.notify("Escolle o cultivo", type="warning")
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
                    datos = DatosAbonado(
                        cultivo_id=cultivo.value, data_inicio=inicio,
                        data_fin=parsear_data(data_fin.value), superficie_ha=superficie.ha,
                        tipo_fertilizacion=tipo.value or "", metodo=metodo.value or "",
                        boas_practicas=list(boas.value or []), fertilizante_id=abono.value,
                        dose=parsear_decimal(dose.value), unidade=unidade.value,
                        xestion_sostible=xestion.value, aplicacion_lodos=lodos.value,
                        albaran_factura=albaran.value or None, aplicador_persoa_id=aplicador.value,
                        maquina_id=maquina.value, empresa_servizos_regfer=empresa.value or None,
                        horas=parsear_decimal(horas.value), notas=notas.value or None)
                    existente = session.get(Abonado, editando["id"]) if editando["id"] else None
                    if existente is None:
                        crear_abonado(session, actor_actual, datos)
                    else:
                        actualizar_abonado(session, actor_actual, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(a: Abonado | None) -> None:
        editando["id"] = a.id if a else None
        titulo.text = "Editar abonado" if a else "Apuntar abonado"
        cultivo.value = a.cultivo_id if a else None
        data_inicio.value = (a.data_inicio if a else date.today()).isoformat()
        data_fin.value = a.data_fin.isoformat() if a and a.data_fin != a.data_inicio else ""
        superficie.establecer(a.superficie_ha if a else None)
        abono.value = a.fertilizante_id if a else None
        dose.value = f"{a.dose:g}" if a and a.dose else ""
        unidade.value = (a.unidade if a and a.unidade else "17")
        tipo.value = a.tipo_fertilizacion if a else None
        metodo.value = a.metodo if a else None
        boas.value = [b.codigo for b in a.boas_practicas] if a else []
        xestion.value = a.xestion_sostible if a else False
        lodos.value = a.aplicacion_lodos if a else False
        albaran.value = (a.albaran_factura or "") if a else ""
        aplicador.value = (a.aplicador_persoa_id if a.aplicador_persoa_id in persoas
                           else None) if a else proposta_quen(horta_id)
        horas.value = f"{a.horas:g}" if a and a.horas else ""
        maquina.value = a.maquina_id if a else None
        empresa.value = (a.empresa_servizos_regfer or "") if a else ""
        notas.value = (a.notas or "") if a else ""
        calcular()
        dialogo.open()

    return abrir
