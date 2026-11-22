"""Sección Plan de empresa (paso 16): datos do Anexo III, conta a 5 anos proposta desde o
real, investimento (Anexo V), financiamento, indicadores, métricas e seguimento."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.plan_empresa import PlanEmpresa, PlanFinanciamento, PlanInvestimento
from horta.services.errors import OperacionNonPermitidaError
from horta.services.plan_empresa import (
    FONTES,
    PARTIDAS,
    actualizar_plan,
    avisos_plan,
    conta,
    crear_plan,
    engadir_financiamento,
    engadir_investimento,
    gardar_anos,
    indicadores,
    listar_plans,
    metricas,
    quitar,
    seguimento,
    xerar_anexos,
)
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual


def _e(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def _accion(funcion: Any) -> None:
    """Executa unha acción sobre o plan e recarga se vai ben."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        ok = executar_accion(session, lambda: funcion(session, actor))
    if ok:
        ui.navigate.reload()


def seccion_plan_empresa(horta_id: int, pode_editar: bool) -> None:
    if not pode_editar:
        ui.label("Só quen pode editar a explotación ve o plan de empresa.").classes(
            "texto-suave")
        return
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        plans = listar_plans(session, actor, horta_id)
        ano_real = date.today().year - 1
        met = metricas(session, actor, horta_id, ano_real)
        segue = {p.id: seguimento(session, actor, p) for p in plans}

    with ui.row().classes("items-end gap-2"):
        titulo = ui.input("Título do novo plan").classes("w-64")
        ano1 = ui.input("Ano 1", value=str(date.today().year + 1)).classes("w-24")
        ui.button("Novo plan", icon="add", on_click=lambda: _accion(
            lambda s, a: crear_plan(s, a, horta_id, titulo.value or "",
                                    int(parsear_decimal(ano1.value) or date.today().year))))
    ui.label("Os 5 anos propóñense iguais ao ano pasado en Cartos; cámbiaos na conta."
             ).classes("texto-suave text-caption")

    for plan in plans:
        with ui.expansion(f"{plan.titulo} · ano 1: {plan.ano_inicio}", icon="business_center"
                          ).classes("w-full tarxeta q-mt-md"):
            _plan(plan, segue[plan.id])

    with ui.expansion(f"Métricas da explotación en {ano_real}", icon="insights").classes(
            "w-full tarxeta q-mt-md"):
        for nome, valores, unidade in (("Rendemento", met.rendemento, " kg/ha"),
                                       ("Prezo medio de venda", met.prezo_medio, " €"),
                                       ("Refugo", met.refugo_pct, " %")):
            ui.label(nome).classes("text-weight-bold")
            if not valores:
                ui.label("Sen datos").classes("texto-suave")
            for clave, valor in valores.items():
                ui.label(f"{clave}: {valor:g}{unidade}")
        ui.label(f"Horas de traballo: {met.horas:g} ({met.uta:g} UTA)")
        ui.label("Punto morto (vendas para cubrir custos): "
                 + (_e(met.punto_morto) if met.punto_morto is not None else "sen datos"))


def _plan(plan: PlanEmpresa, segue: list) -> None:
    ind = indicadores(plan)
    for aviso in avisos_plan(plan):
        ui.label(aviso).classes("etiqueta-aviso")
    with ui.row().classes("gap-6"):
        ui.label(f"Investimento: {_e(ind.investimento)} (con IVE {_e(ind.investimento_con_iva)})")
        ui.label(f"VAN: {_e(ind.van)}")
        ui.label(f"TIR: {ind.tir:.1%}" if ind.tir is not None else "TIR: —")
        ui.label(f"Pay-back: {ind.payback} anos" if ind.payback else "Pay-back: —")

    ui.label("Datos (Anexo III)").classes("text-subtitle1 text-weight-bold q-mt-md")
    nova = ui.checkbox("Empresa nova", value=plan.empresa_nova)
    cnae = ui.input("CNAE", value=plan.cnae or "").classes("w-32")
    textos = {c: ui.textarea(e, value=getattr(plan, c) or "").classes("w-full")
              for c, e in (("descricion", "1. Descrición, obxectivos e finalidade"),
                           ("proceso", "2. Proceso e medios humanos e materiais"),
                           ("formacion", "4. Formación do promotor"))}
    with ui.row().classes("gap-2"):
        utas = {c: ui.input(e, value=f"{getattr(plan, c):g}").classes("w-28")
                for c, e in (("uta_mantidas", "UTA mantidas"), ("uta_creadas", "UTA creadas"),
                             ("uta_mulleres", "…mulleres"), ("uta_mozas", "…mozas"),
                             ("uta_maiores", "…maiores"),
                             ("uta_discapacidade", "…discapacidade"),
                             ("uta_outros", "…outros"))}
    taxa = ui.input("Taxa para o VAN (p.ex. 0,03)", value=f"{plan.taxa_desconto:g}").classes(
        "w-48")
    ui.button("Gardar os datos", icon="check", on_click=lambda: _accion(
        lambda s, a: actualizar_plan(
            s, a, s.get(PlanEmpresa, plan.id), empresa_nova=nova.value,
            cnae=cnae.value or None, **{c: t.value or None for c, t in textos.items()},
            **{c: parsear_decimal(u.value) or 0 for c, u in utas.items()},
            taxa_desconto=parsear_decimal(taxa.value) or 0))).props("outline")

    ui.label("Conta de explotación (6)").classes("text-subtitle1 text-weight-bold q-mt-md")
    filas = conta(plan)
    entradas: dict[int, list[ui.input]] = {a.ano_n: [] for a in filas}
    with ui.grid(columns=6).classes("w-full gap-1 items-center"):
        for texto in ("", *(f"Ano {a.ano_n} ({a.ano})" for a in filas)):
            ui.label(texto).classes("text-weight-bold text-caption")
        for nome, campo in (("A) Vendas", "vendas"), ("B) Variables", "variables"),
                            ("C) Fixos", "fixos")):
            ui.label(nome)
            for a in filas:
                entradas[a.ano_n].append(
                    ui.input(value=f"{getattr(a, campo):g}").props("dense"))
        for nome, campo in (("D) Amortizacións", "amortizacions"), ("E) Marxe", "marxe"),
                            ("F) Financeiro", "financeiro"), ("G) Beneficio", "beneficio")):
            ui.label(nome)
            for a in filas:
                ui.label(_e(getattr(a, campo)))

    def gardar_conta(session: Any, actor: Any) -> None:
        valores = {n: (parsear_decimal(v.value) or 0, parsear_decimal(b.value) or 0,
                       parsear_decimal(c.value) or 0) for n, (v, b, c) in entradas.items()}
        gardar_anos(session, actor, session.get(PlanEmpresa, plan.id), valores)

    ui.button("Gardar a conta", icon="check", on_click=lambda: _accion(gardar_conta)).props(
        "outline")

    ui.label("Investimento (Anexo V)").classes("text-subtitle1 text-weight-bold q-mt-md")
    for i in sorted(plan.investimentos, key=lambda i: i.partida):
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{PARTIDAS[i.partida]} · {i.concepto}: {_e(i.importe_sen_iva)} + "
                     f"{i.iva_pct:g} % IVE · {i.ofertas} ofertas")
            ui.button(icon="delete", on_click=lambda i=i: _accion(
                lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                    s.get(PlanInvestimento, i.id)))).props(
                "flat dense round size=sm color=negative")
    with ui.row().classes("items-end gap-2"):
        partida = ui.select(PARTIDAS, label="Partida", value="3").classes("w-56")
        concepto = ui.input("Concepto").classes("w-48")
        importe = ui.input("Sen IVE (€)").classes("w-28")
        iva = ui.input("IVE %", value="21").classes("w-20")
        vida = ui.input("Vida útil (anos)", value="10").classes("w-28")
        ofertas = ui.input("Ofertas", value="3").classes("w-20")
        ui.button("Engadir", icon="add", on_click=lambda: _accion(
            lambda s, a: engadir_investimento(
                s, a, s.get(PlanEmpresa, plan.id), partida.value, concepto.value or "",
                parsear_decimal(importe.value) or 0, parsear_decimal(iva.value) or 0,
                int(parsear_decimal(vida.value) or 0), int(parsear_decimal(ofertas.value) or 0)
            ))).props("outline")

    ui.label("Financiamento (5)").classes("text-subtitle1 text-weight-bold q-mt-md")
    for f in plan.financiamento:
        with ui.row().classes("items-center gap-2"):
            extra = f" · {f.xuro_pct:g} % a {f.anos} anos" if f.tipo == "prestamo" else ""
            ui.label(f"{FONTES[f.tipo]}: {_e(f.importe)}{extra}")
            ui.button(icon="delete", on_click=lambda f=f: _accion(
                lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                    s.get(PlanFinanciamento, f.id)))).props(
                "flat dense round size=sm color=negative")
    with ui.row().classes("items-end gap-2"):
        fonte = ui.select(FONTES, label="Fonte", value="propios").classes("w-48")
        canto = ui.input("Importe (€)").classes("w-28")
        xuro = ui.input("Xuro % (préstamo)").classes("w-32")
        anos = ui.input("Anos (préstamo)").classes("w-28")
        ui.button("Engadir", icon="add", on_click=lambda: _accion(
            lambda s, a: engadir_financiamento(
                s, a, s.get(PlanEmpresa, plan.id), fonte.value,
                parsear_decimal(canto.value) or 0, parsear_decimal(xuro.value),
                int(parsear_decimal(anos.value) or 0) or None))).props("outline")

    if segue:
        ui.label("Seguimento: previsto e real").classes("text-subtitle1 text-weight-bold q-mt-md")
        for s in segue:
            ui.label(f"{s.ano}: vendas {_e(s.previsto_vendas)} previstas, {_e(s.real_vendas)} "
                     f"reais · marxe {_e(s.previsto_marxe)} prevista, {_e(s.real_marxe)} real")

    def descargar() -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            try:
                datos = xerar_anexos(session, actor, plan.id)
            except OperacionNonPermitidaError as erro:
                ui.notify(str(erro), type="negative")
                return
        ui.download.content(datos, f"plan-empresa-{plan.id}.xlsx")

    ui.button("Descargar Anexo III e V (Excel)", icon="download", on_click=descargar).classes(
        "q-mt-md")
