"""Sección Cartos: resumo do ano,
pendente de cobrar e de pagar por persoa, e os outros gastos e ingresos."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.cartos import ApunteCartos
from horta.services.cartos import (
    CATEGORIAS,
    PERIODOS,
    TIPOS,
    DatosApunte,
    actualizar_apunte,
    crear_apunte,
    dar_de_baixa_apunte,
    listar_apuntes,
    pendente_por_persoa,
    periodo,
    periodos_recentes,
    resumo_periodo,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import listar_persoas, nome_completo
from horta.ui.accions import executar_accion
from horta.ui.campo_pago import CampoPago
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def _euros(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def seccion_cartos(horta_id: int, pode_editar: bool) -> None:
    if not pode_editar:
        ui.label("Só quen pode editar a explotación ve os cartos.").classes("texto-suave")
        return
    estado: dict[str, Any] = {"tipo": "ano", "periodo": periodo("ano", date.today())}

    @ui.refreshable
    def contido() -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            actual = estado["periodo"]
            resumo = resumo_periodo(session, actor, horta_id, actual)
            saldos = pendente_por_persoa(session, actor, horta_id)
            apuntes = listar_apuntes(session, actor, horta_id, actual.desde, actual.ata)
            nomes = {p.id: nome_completo(p)
                     for p in listar_persoas(session, actor, horta_id, so_activas=False)}

        with ui.row().classes("w-full gap-4"):
            for titulo, partidas, total in (("Ingresos", resumo.ingresos, resumo.total_ingresos),
                                            ("Gastos", resumo.gastos, resumo.total_gastos)):
                with ui.column().classes("tarxeta col gap-1"):
                    ui.label(titulo).classes("text-subtitle1 text-weight-bold")
                    if not partidas:
                        ui.label("Nada apuntado neste período").classes("texto-suave")
                    for nome, valor in partidas.items():
                        with ui.row().classes("w-full justify-between"):
                            ui.label(nome)
                            ui.label(_euros(valor))
                    with ui.row().classes("w-full justify-between text-weight-bold"):
                        ui.label("Total")
                        ui.label(_euros(total))
        with ui.column().classes("tarxeta w-full gap-1 q-mt-md"):
            ui.label(f"Resultado ({resumo.periodo.nome}): {_euros(resumo.resultado)}").classes(
                "text-subtitle1 text-weight-bold")
            if resumo.custos.man_de_obra_propia:
                ui.label(f"Sen contar as horas do titular e a familia (non se pagan): "
                         f"{_euros(resumo.resultado_sen_man_propia)}").classes("texto-suave")
            if resumo.custos.sen_custo:
                ui.label(f"{resumo.custos.sen_custo} traballos con horas quedan sen contar: "
                         "falta o custo da hora da persoa ou da máquina (Equipo, Maquinaria)"
                         ).classes("etiqueta-aviso")

        ui.label("Pendente de cobrar e de pagar").classes(
            "text-subtitle1 text-weight-bold q-mt-md")
        if not saldos:
            ui.label("Non hai nada pendente.").classes("texto-suave")
        for persoa_id, saldo in sorted(saldos.items(), key=lambda par: -abs(par[1])):
            quen = nomes.get(persoa_id or 0)
            if quen is None:
                texto = (f"Sen persoa: pendente de cobrar {_euros(saldo)}" if saldo > 0
                         else f"Sen persoa: pendente de pagar {_euros(-saldo)}")
            else:
                texto = (f"{quen} débeche {_euros(saldo)}" if saldo > 0
                         else f"Débeslle a {quen} {_euros(-saldo)}")
            ui.label(texto)

        with ui.row().classes("w-full items-center justify-between q-mt-md"):
            ui.label("Outros gastos e ingresos").classes("text-subtitle1 text-weight-bold")
            ui.button("Novo", icon="add", on_click=lambda: abrir(None))
        filas = [{"id": a.id, "data": f"{a.data:%d/%m/%Y}", "tipo": TIPOS[a.tipo],
                  "categoria": CATEGORIAS[a.categoria], "concepto": a.concepto,
                  "importe": _euros(a.importe), "quen": nomes.get(a.persoa_id or 0, ""),
                  "pago": "Si" if a.data_pago else "Pendente"} for a in apuntes]
        columnas = [{"name": c, "label": e, "field": c, "align": "left"} for c, e in (
            ("data", "Data"), ("tipo", "Tipo"), ("categoria", "Categoría"),
            ("concepto", "Concepto"), ("importe", "Importe"), ("quen", "Quen"),
            ("pago", "Cobrado ou pagado"))]
        ui.table(columns=columnas, rows=filas, row_key="id", selection="single",
                 on_select=lambda e: abrir(e.selection[0]["id"]) if e.selection else None
                 ).classes("w-full").props(TEXTOS_TABOA)

    with ui.row().classes("items-center gap-2"):
        def opcions() -> dict[str, str]:
            return {p.desde.isoformat(): p.nome
                    for p in periodos_recentes(estado["tipo"], date.today())}

        def cambiar_tipo(tipo: str) -> None:
            estado["tipo"] = tipo
            escoller.options = opcions()
            escoller.value = periodo(tipo, date.today()).desde.isoformat()
            escoller.update()

        def cambiar_periodo(desde: str | None) -> None:
            if desde is not None:
                estado["periodo"] = periodo(estado["tipo"], date.fromisoformat(desde))
                contido.refresh()

        ui.select(PERIODOS, label="Resumo por", value="ano",
                  on_change=lambda e: cambiar_tipo(e.value)).classes("min-w-32")
        escoller = ui.select(opcions(), label="Período", value=estado["periodo"].desde.isoformat(),
                             on_change=lambda e: cambiar_periodo(e.value)).classes("min-w-64")

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("").classes("text-h6")
        tipo = ui.select(TIPOS, label="Tipo", value="gasto").classes("w-full")
        categoria = ui.select(CATEGORIAS, label="Categoría", value="outro").classes("w-full")
        concepto = ui.input("Concepto").classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data("Data").classes(remove="w-full", add="col")
            importe = ui.input("Importe (€)").classes("col")
        persoa = ui.select({}, label="A quen ou de quen (opcional)", clearable=True).classes(
            "w-full")
        albaran = ui.input("Factura ou recibo").classes("w-full")
        pago = CampoPago("Cobrado ou pagado")
        notas = ui.textarea("Notas").classes("w-full")
        editando: dict[str, int | None] = {"id": None}

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if dia is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    datos = DatosApunte(
                        tipo=tipo.value, categoria=categoria.value, concepto=concepto.value or "",
                        data=dia, importe=parsear_decimal(importe.value) or 0,
                        persoa_id=persoa.value, albaran_factura=albaran.value or None,
                        data_pago=pago.valor(dia), notas=notas.value or None)
                    existente = (session.get(ApunteCartos, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        crear_apunte(session, actor, horta_id, datos)
                    else:
                        actualizar_apunte(session, actor, existente, datos)

                if executar_accion(session, accion):
                    dialogo.close()
                    contido.refresh()

        def dar_de_baixa() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                apunte = session.get(ApunteCartos, editando["id"]) if editando["id"] else None
                if actor is None or apunte is None:
                    return
                if executar_accion(session, lambda: dar_de_baixa_apunte(session, actor, apunte)):
                    dialogo.close()
                    contido.refresh()

        with ui.row().classes("w-full justify-between"):
            with ui.row():
                ui.button("Gardar", icon="check", on_click=gardar)
                ui.button("Cancelar", on_click=dialogo.close).props("flat")
            baixa = ui.button("Dar de baixa", icon="delete", on_click=lambda: (
                confirmar_eliminacion("Dar de baixa este apunte?", dar_de_baixa))).props(
                "flat color=negative")

    def abrir(apunte_id: int | None) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            apunte = session.get(ApunteCartos, apunte_id) if apunte_id else None
            persoa.options = {p.id: nome_completo(p)
                              for p in listar_persoas(session, actor, horta_id)}
        persoa.update()
        editando["id"] = apunte.id if apunte else None
        titulo.text = "Editar apunte" if apunte else "Outro gasto ou ingreso"
        tipo.value = apunte.tipo if apunte else "gasto"
        categoria.value = apunte.categoria if apunte else "outro"
        concepto.value = apunte.concepto if apunte else ""
        data.value = (apunte.data if apunte else date.today()).isoformat()
        importe.value = f"{apunte.importe:g}" if apunte else ""
        persoa.value = apunte.persoa_id if apunte else None
        albaran.value = (apunte.albaran_factura or "") if apunte else ""
        pago.poñer(apunte.data_pago if apunte else None, apunte is None)
        notas.value = (apunte.notas or "") if apunte else ""
        baixa.set_visibility(apunte is not None)
        dialogo.open()

    contido()
