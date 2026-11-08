"""Sección Plan de empresa (paso 16): datos do Anexo III, conta a 5 anos proposta desde o
real, investimento (Anexo V) coas súas ofertas (Anexo VI-A e VI-B), financiamento,
indicadores, o que lle falta, a documentación do art. 18, métricas e seguimento."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.persoa import Persoa
from horta.models.plan_empresa import (
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanOferta,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import con_papel, nome_completo
from horta.services.plan_empresa import (
    FONTES,
    PARTIDAS,
    TIPOLOXIAS,
    Documento,
    actualizar_plan,
    ano_de_referencia,
    avisos_plan,
    conta,
    crear_plan,
    documentos_plan,
    engadir_financiamento,
    engadir_investimento,
    engadir_oferta,
    faltas_plan,
    gardar_anos,
    indicadores,
    listar_plans,
    metricas,
    quitar,
    seguimento,
    xerar_anexos,
)
from horta.ui.accions import executar_accion
from horta.ui.formato_descarga import descargar_informe, selector_formato
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
        ano_real = ano_de_referencia(session, actor, horta_id)
        met = metricas(session, actor, horta_id, ano_real)
        segue = {p.id: seguimento(session, actor, p) for p in plans}
        faltas = {p.id: faltas_plan(session, actor, p) for p in plans}
        docs = {p.id: documentos_plan(session, actor, p) for p in plans}
        provedores = con_papel(session, horta_id, "provedor")
        nomes = {p.id: nome_completo(p) for p in
                 session.query(Persoa).filter_by(horta_id=horta_id)}

    with ui.row().classes("items-end gap-2"):
        titulo = ui.input("Título do novo plan").classes("w-64")
        ano1 = ui.input("Ano 1", value=str(date.today().year + 1)).classes("w-24")
        ui.button("Novo plan", icon="add", on_click=lambda: _accion(
            lambda s, a: crear_plan(s, a, horta_id, titulo.value or "",
                                    int(parsear_decimal(ano1.value) or date.today().year))))
    referencia = "ao ano pasado" if ano_real < date.today().year else (
        f"ao que levas de {ano_real}")
    ui.label(f"Os 5 anos propóñense iguais {referencia} en Contas; cámbiaos na conta."
             ).classes("texto-suave text-caption")

    for plan in plans:
        with ui.expansion(f"{plan.titulo} · ano 1: {plan.ano_inicio}", icon="business_center"
                          ).classes("w-full tarxeta q-mt-md"):
            _plan(plan, segue[plan.id], faltas[plan.id], docs[plan.id],
                  {p.id: nome_completo(p) for p in provedores}, nomes)

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


def _plan(plan: PlanEmpresa, segue: list, faltas: list[str], docs: list[Documento],
          provedores: dict[int, str], nomes: dict[int, str]) -> None:
    ind = indicadores(plan)
    if faltas:
        ui.label("Para presentalo falta: " + "; ".join(faltas) + ".").classes(
            "etiqueta-aviso")
    for aviso in avisos_plan(plan):
        ui.label(aviso).classes("etiqueta-aviso")
    with ui.row().classes("gap-6"):
        ui.label(f"Investimento: {_e(ind.investimento)} (con IVE {_e(ind.investimento_con_iva)})")
        ui.label(f"VAN: {_e(ind.van)}")
        ui.label(f"TIR: {ind.tir:.1%}" if ind.tir is not None else "TIR: —")
        ui.label(f"Pay-back: {ind.payback} anos" if ind.payback else "Pay-back: —")

    ui.label("Datos (Anexo III)").classes("text-subtitle1 text-weight-bold q-mt-md")
    tipoloxia = ui.select({k: t.texto for k, t in TIPOLOXIAS.items()}, label="Tipoloxía",
                          value=plan.tipoloxia, clearable=True).classes("w-full")
    if plan.tipoloxia in TIPOLOXIAS:
        ui.label(f"Axuda: {TIPOLOXIAS[plan.tipoloxia].axuda}").classes(
            "texto-suave text-caption")
    with ui.row().classes("gap-2"):
        proxecto = {c: ui.input(e, value=str(getattr(plan, c) or "")).classes("w-40")
                    for c, e in (("expediente", "Nº de expediente"),
                                 ("anualidade", "Anualidade"), ("submedida", "Submedida"),
                                 ("gdr", "Grupo (GDR)"))}
    ui.label("O expediente, a anualidade e a submedida dáos o GDR.").classes(
        "texto-suave text-caption")
    with ui.row().classes("items-end gap-2"):
        nova = ui.checkbox("Empresa nova", value=plan.empresa_nova)
        cnae = ui.input("CNAE", value=plan.cnae or "").classes("w-32")
        participada = ui.checkbox("Participa ou está participada nun 25 % ou máis",
                                  value=plan.participada)
    with ui.row().classes("gap-2"):
        empresa = {c: ui.input(e, value="" if getattr(plan, c) is None
                               else f"{getattr(plan, c):g}").classes("w-36")
                   for c, e in (("traballadores", "Nº de traballadores"),
                                ("facturacion", "Facturación (€)"), ("balance", "Balance (€)"))}
    recuperable = ui.checkbox("O IVE é recuperable (se non o é, o investimento conta con IVE)",
                      value=plan.iva_recuperable)
    textos = {c: ui.textarea(e, value=getattr(plan, c) or "").classes("w-full")
              for c, e in (("descricion", "1. Descrición, obxectivos e finalidade"),
                           ("proceso", "2. Proceso e medios humanos e materiais"),
                           ("formacion", "4. Formación do promotor"),
                           ("situacion_partida", "Memoria: situación de partida"),
                           ("metodoloxia", "Memoria: metodoloxía de traballo"),
                           ("mercado", "Memoria: mercado e clientes"))}
    with ui.row().classes("gap-2"):
        utas = {c: ui.input(e, value=f"{getattr(plan, c):g}").classes("w-28")
                for c, e in (("uta_mantidas", "UTA mantidas"), ("uta_creadas", "UTA creadas"),
                             ("uta_mulleres", "…mulleres"), ("uta_mozas", "…mozas"),
                             ("uta_maiores", "…maiores"),
                             ("uta_discapacidade", "…discapacidade"),
                             ("uta_outros", "…outros"))}
    taxa = ui.input("Taxa para o VAN (p.ex. 0,03)", value=f"{plan.taxa_desconto:g}").classes(
        "w-48")
    ui.label("Declaracións do Anexo VI-B").classes("text-weight-medium")
    declaracions = {c: ui.checkbox(e, value=getattr(plan, c))
                    for c, e in (("ofertas_autenticas", "As ofertas son auténticas"),
                                 ("sen_vinculo_promotor", "Non hai vinculación cos provedores"),
                                 ("sen_vinculo_entre_provedores",
                                  "Os provedores de cada gasto non están vinculados entre "
                                  "eles"))}
    ui.button("Gardar os datos", icon="check", on_click=lambda: _accion(
        lambda s, a: actualizar_plan(
            s, a, s.get(PlanEmpresa, plan.id), empresa_nova=nova.value,
            cnae=cnae.value or None, tipoloxia=tipoloxia.value or None,
            expediente=proxecto["expediente"].value or None,
            anualidade=int(parsear_decimal(proxecto["anualidade"].value) or 0) or None,
            submedida=proxecto["submedida"].value or None, gdr=proxecto["gdr"].value or None,
            participada=participada.value, iva_recuperable=recuperable.value,
            **{c: parsear_decimal(e.value) for c, e in empresa.items()},
            **{c: t.value or None for c, t in textos.items()},
            **{c: d.value for c, d in declaracions.items()},
            **{c: parsear_decimal(u.value) or 0 for c, u in utas.items()},
            taxa_desconto=parsear_decimal(taxa.value) or 0))).props("outline")

    ui.label("Conta de explotación (6)").classes("text-subtitle1 text-weight-bold q-mt-md")
    filas = conta(plan)
    entradas: dict[int, list[ui.input]] = {a.ano_n: [] for a in filas}
    with ui.grid(columns=6).classes("w-full gap-1 items-center"):
        for texto in ("", *(f"Ano {a.ano_n} ({a.ano})" for a in filas)):
            ui.label(texto).classes("text-weight-bold text-caption")
        financeiros = {a.ano_n: a.ingresos_financeiros for a in plan.anos}
        for nome, campo in (("A) Vendas", "vendas"), ("B) Variables", "variables"),
                            ("C) Fixos", "fixos"), ("Ingresos financeiros", "")):
            ui.label(nome)
            for a in filas:
                valor = getattr(a, campo) if campo else financeiros.get(a.ano_n, 0)
                entradas[a.ano_n].append(ui.input(value=f"{valor:g}").props("dense"))
        for nome, campo in (("D) Amortizacións", "amortizacions"), ("E) Marxe", "marxe"),
                            ("F) Financeiro", "financeiro"), ("G) Beneficio", "beneficio")):
            ui.label(nome)
            for a in filas:
                ui.label(_e(getattr(a, campo)))

    def gardar_conta(session: Any, actor: Any) -> None:
        valores = {n: (parsear_decimal(v.value) or 0, parsear_decimal(b.value) or 0,
                       parsear_decimal(c.value) or 0, parsear_decimal(f.value) or 0)
                   for n, (v, b, c, f) in entradas.items()}
        gardar_anos(session, actor, session.get(PlanEmpresa, plan.id), valores)

    ui.button("Gardar a conta", icon="check", on_click=lambda: _accion(gardar_conta)).props(
        "outline")

    ui.label("Investimento (Anexo V)").classes("text-subtitle1 text-weight-bold q-mt-md")
    for i in sorted(plan.investimentos, key=lambda i: i.partida):
        with ui.row().classes("items-center gap-2"):
            ui.label(f"{PARTIDAS[i.partida]} · {i.concepto}: {_e(i.importe_sen_iva)} + "
                     f"{i.iva_pct:g} % IVE")
            ui.button(icon="delete", on_click=lambda i=i: _accion(
                lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                    s.get(PlanInvestimento, i.id)))).props(
                "flat dense round size=sm color=negative")
        _ofertas(plan, i, provedores, nomes)
    with ui.row().classes("items-end gap-2"):
        partida = ui.select(PARTIDAS, label="Partida", value="3").classes("w-56")
        concepto = ui.input("Concepto").classes("w-48")
        importe = ui.input("Sen IVE (€)").classes("w-28")
        iva = ui.input("IVE %", value="21").classes("w-20")
        vida = ui.input("Vida útil (anos)", value="10").classes("w-28")
        motivo = ui.input("Se non hai tres ofertas, por que").classes("w-64")
        ui.button("Engadir", icon="add", on_click=lambda: _accion(
            lambda s, a: engadir_investimento(
                s, a, s.get(PlanEmpresa, plan.id), partida.value, concepto.value or "",
                parsear_decimal(importe.value) or 0, parsear_decimal(iva.value) or 0,
                int(parsear_decimal(vida.value) or 0), motivo.value or None
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

    ui.label("Documentación (art. 18)").classes("text-subtitle1 text-weight-bold q-mt-md")
    for doc in docs:
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.icon("check_circle" if doc.da_app else "upload_file").classes(
                "text-positive" if doc.da_app else "text-grey")
            ui.label(f"{doc.letra}) {doc.texto}" + ("" if doc.da_app else " · achégao ti")
                     ).classes("text-body2")

    if segue:
        ui.label("Seguimento: previsto e real").classes("text-subtitle1 text-weight-bold q-mt-md")
        for s in segue:
            ui.label(f"{s.ano}: vendas {_e(s.previsto_vendas)} previstas, {_e(s.real_vendas)} "
                     f"reais · marxe {_e(s.previsto_marxe)} prevista, {_e(s.real_marxe)} real")

    formato = selector_formato()

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
        descargar_informe(
            datos,
            formato.value or "xlsx",
            f"plan-empresa-{plan.id}",
            "Plan de empresa",
            "plan",
        )

    ui.button("Descargar Anexo III e V", icon="download", on_click=descargar).classes(
        "q-mt-md")


def _ofertas(plan: PlanEmpresa, investimento: PlanInvestimento, provedores: dict[int, str],
             nomes: dict[int, str]) -> None:
    """As ofertas dun concepto (Anexo VI-A) e o formulario para engadir outra."""
    with ui.column().classes("q-ml-lg gap-1"):
        if investimento.motivo_sen_ofertas:
            ui.label(f"Sen tres ofertas: {investimento.motivo_sen_ofertas}").classes(
                "texto-suave text-caption")
        for o in investimento.ofertas:
            with ui.row().classes("items-center gap-2"):
                ui.label(f"{'✔ ' if o.elixida else ''}{nomes.get(o.provedor_id, '')}: "
                         f"{_e(o.importe_sen_iva)}"
                         + (f" · {o.criterio}" if o.criterio else "")).classes("text-body2")
                ui.button(icon="delete", on_click=lambda o=o: _accion(
                    lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                        s.get(PlanOferta, o.id)))).props(
                    "flat dense round size=sm color=negative")
        if not provedores:
            ui.label("Para engadir ofertas, crea os provedores en Persoas → Contactos.").classes(
                "texto-suave text-caption")
            return
        with ui.row().classes("items-end gap-2"):
            provedor = ui.select(provedores, label="Provedor").classes("w-48")
            importe = ui.input("Sen IVE (€)").classes("w-28")
            elixida = ui.checkbox("Elixida")
            criterio = ui.input("Criterio").classes("w-36")
            xustificacion = ui.input("Por que non a máis barata").classes("w-48")
            ui.button("Oferta", icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_oferta(
                    s, a, s.get(PlanEmpresa, plan.id), s.get(PlanInvestimento,
                                                             investimento.id),
                    provedor.value, parsear_decimal(importe.value) or 0, elixida.value,
                    criterio.value or None, xustificacion.value or None))).props(
                "outline dense")
