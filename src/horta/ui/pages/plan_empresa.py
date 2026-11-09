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
    PlanActividade,
    PlanEmpresa,
    PlanFinanciamento,
    PlanInvestimento,
    PlanObxectivo,
    PlanOferta,
    PlanVenda,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.lotes import CANLES
from horta.services.persoas import con_papel, nome_completo
from horta.services.plan_empresa import (
    ETIQUETAS_MEMORIA,
    FONTES,
    PARTIDAS,
    SECCIONS_MEMORIA,
    TIPOLOXIAS,
    Documento,
    MarxeVenda,
    MesTesouraria,
    actualizar_plan,
    ano_de_referencia,
    avisos_plan,
    conta,
    crear_plan,
    documentos_plan,
    engadir_actividade,
    engadir_financiamento,
    engadir_investimento,
    engadir_obxectivo,
    engadir_oferta,
    engadir_venda,
    faltas_memoria,
    faltas_plan,
    gardar_anos,
    indicadores,
    listar_plans,
    marxes_por_venda,
    meses_de,
    metricas,
    propor_vendas_do_real,
    quitar,
    seguimento,
    tesouraria,
    vendas_do_ano,
    xerar_anexos,
    xerar_memoria,
)
from horta.ui.accions import executar_accion
from horta.ui.formato_descarga import descargar_informe, selector_formato
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

MESES_TESOURARIA = [
    "Xan", "Feb", "Mar", "Abr", "Mai", "Xuñ",
    "Xul", "Ago", "Set", "Out", "Nov", "Dec",
]


class _ValorFixo:
    """Simula un compoñente de entrada para valores que se amosan só como texto."""

    def __init__(self, valor: Any) -> None:
        self.value = str(valor)


def _e(valor: float) -> str:
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def _n(valor: float) -> str:
    """Número curto con coma decimal (1,5; 62,5)."""
    return f"{valor:g}".replace(".", ",")


def texto_venda(v: PlanVenda) -> str:
    """Texto para a liña dunha venda prevista en detalle."""
    canle = CANLES.get(v.canle, v.canle)
    importe, _ = vendas_do_ano(v, 1)
    partes = [
        f"{v.produto} · {canle}: {_n(v.cantidade)} {v.unidade} a {_n(v.prezo)} € "
        f"(ano 1: {_e(importe)})"
    ]
    if v.custo_unitario is not None:
        partes.append(f"custo {_n(v.custo_unitario)} €/{v.unidade}")
    cq = v.crece_cantidade_pct or 0
    cp = v.crece_prezo_pct or 0
    if cq != 0 or cp != 0:
        if cq != 0 and cp != 0:
            x = f"{_n(cq)}" if cq == cp else f"{_n(cq)} cantidade, {_n(cp)} prezo"
        elif cq != 0:
            x = f"{_n(cq)}"
        else:
            x = f"{_n(cp)}"
        partes.append(f"crece {x} %/ano")
    meses = meses_de(v.meses)
    if meses != list(range(1, 13)):
        partes.append(f"meses {', '.join(str(m) for m in meses)}")
    return " · ".join(partes)


def texto_marxe(m: MarxeVenda) -> str:
    """Texto para a liña da marxe por venda no ano 1."""
    pct = f"{_n(m.marxe_pct)} %" if m.marxe_pct is not None else "—"
    return (
        f"{m.produto} · {m.canle}: vende {_e(m.importe)}, custa {_e(m.custo)}, "
        f"deixa {_e(m.marxe)} ({pct})"
    )


def opcions_tesouraria(meses: list[MesTesouraria]) -> dict[str, Any]:
    """Opcións para o gráfico de tesouraría mes a mes do ano 1."""
    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 0},
        "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
        "xAxis": {"type": "category", "data": MESES_TESOURARIA},
        "yAxis": {"type": "value"},
        "series": [
            {"name": "Cobros", "type": "bar", "data": [m.cobros for m in meses]},
            {"name": "Pagos", "type": "bar", "data": [m.pagos for m in meses]},
            {"name": "Saldo acumulado", "type": "line", "data": [m.saldo for m in meses]},
        ],
    }


def texto_actividade(a: PlanActividade) -> str:
    """Texto para a liña dunha actividade do calendario."""
    rango = f"Mes {a.mes_inicio}" if a.mes_inicio == a.mes_fin else (
        f"Mes {a.mes_inicio}–{a.mes_fin}"
    )
    responsable = getattr(a, "responsable", None)
    resp = f" · {responsable}" if responsable else ""
    return f"{rango}: {a.actividade}{resp}"


def texto_obxectivo(o: PlanObxectivo) -> str:
    """Texto para a liña dun obxectivo co seu indicador."""
    res = f"{o.obxectivo} — mídese con {o.indicador}"
    meta = getattr(o, "meta", None)
    if meta:
        res += f" · meta: {meta}"
    prazo = getattr(o, "prazo", None)
    if prazo:
        res += f" · prazo: {prazo}"
    return res


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
                   for c, e in (("traballadores", "Nº de persoas traballadoras"),
                                ("facturacion", "Facturación (€)"), ("balance", "Balance (€)"))}
    recuperable = ui.checkbox("O IVE é recuperable (se non o é, o investimento conta con IVE)",
                      value=plan.iva_recuperable)
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
    ui.label("Declaracións do Anexo VI-B").classes("text-weight-medium")
    declaracions = {c: ui.checkbox(e, value=getattr(plan, c))
                    for c, e in (
                        ("ofertas_autenticas", "As ofertas son auténticas"),
                        ("sen_vinculo_promotor",
                         "Non hai vinculación coas empresas provedoras"),
                        ("sen_vinculo_entre_provedores",
                         "As empresas provedoras de cada gasto non están vinculadas entre elas"),
                    )}
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

    ui.label("Vendas en detalle").classes("text-subtitle1 text-weight-bold q-mt-md")
    ui.label(
        "Se engades as vendas por produto e canle, a conta calcula con elas as vendas de cada "
        "ano (e os custos variables, se pos o custo por unidade)."
    ).classes("texto-suave text-caption")

    for v in plan.vendas_detalle:
        with ui.row().classes("items-center gap-2"):
            ui.label(texto_venda(v))
            ui.button(
                icon="delete",
                on_click=lambda v=v: _accion(
                    lambda s, a: quitar(
                        s, a, s.get(PlanEmpresa, plan.id), s.get(PlanVenda, v.id)
                    )
                ),
            ).props("flat dense round size=sm color=negative")

    with ui.row().classes("items-end gap-2"):
        v_produto = ui.input("Produto").classes("w-40")
        v_unidade = ui.input("Unidade", value="kg").classes("w-20")
        v_canle = ui.select(CANLES, label="Canle", value="explotacion").classes("w-48")
        v_cantidade = ui.input("Cantidade (ano 1)").classes("w-32")
        v_prezo = ui.input("Prezo €/unidade").classes("w-28")
        v_custo = ui.input("Custo €/unidade").classes("w-28")
        v_crece_cant = ui.input("Crece cantidade %/ano").classes("w-36")
        v_crece_prezo = ui.input("Crece prezo %/ano").classes("w-32")
        v_meses = ui.select(
            {m: str(m) for m in range(1, 13)},
            label="Meses de venda",
            multiple=True,
        ).classes("w-40")
        ui.button(
            "Engadir",
            icon="add",
            on_click=lambda: _accion(
                lambda s, a: engadir_venda(
                    s,
                    a,
                    s.get(PlanEmpresa, plan.id),
                    produto=v_produto.value or "",
                    unidade=v_unidade.value or "",
                    canle=v_canle.value or "explotacion",
                    cantidade=parsear_decimal(v_cantidade.value) or 0,
                    prezo=parsear_decimal(v_prezo.value) or 0,
                    custo_unitario=parsear_decimal(v_custo.value),
                    crece_cantidade_pct=parsear_decimal(v_crece_cant.value) or 0,
                    crece_prezo_pct=parsear_decimal(v_crece_prezo.value) or 0,
                    meses=v_meses.value or None,
                )
            ),
        ).props("outline")

    if not plan.vendas_detalle:
        def propor_vendas() -> None:
            resultado = {"n": 0}

            def accion(s: Any, a: Any) -> None:
                ano_ref = ano_de_referencia(s, a, plan.horta_id)
                resultado["n"] = propor_vendas_do_real(
                    s, a, s.get(PlanEmpresa, plan.id), ano_ref
                )

            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: accion(session, actor))
            if ok:
                n = resultado["n"]
                if n > 0:
                    ui.notify(f"Engadíronse {n} vendas")
                    ui.navigate.reload()
                else:
                    ui.notify("Non hai vendas con importe ese ano")

        ui.button("Propoñer desde as vendas reais", on_click=propor_vendas).props("outline")
    else:
        ui.label("Marxe por produto e canle (ano 1)").classes("text-weight-bold q-mt-sm")
        for m in marxes_por_venda(plan):
            ui.label(texto_marxe(m))

    ui.label("Conta de explotación (6)").classes("text-subtitle1 text-weight-bold q-mt-md")
    filas = conta(plan)
    entradas: dict[int, list[Any]] = {a.ano_n: [] for a in filas}
    hai_detalle = bool(plan.vendas_detalle)
    hai_custo = hai_detalle and any(v.custo_unitario is not None for v in plan.vendas_detalle)
    with ui.grid(columns=6).classes("w-full gap-1 items-center"):
        for texto in ("", *(f"Ano {a.ano_n} ({a.ano})" for a in filas)):
            ui.label(texto).classes("text-weight-bold text-caption")
        financeiros = {a.ano_n: a.ingresos_financeiros for a in plan.anos}

        # A) Vendas
        ui.label("A) Vendas")
        for a in filas:
            if hai_detalle:
                ui.label(_e(a.vendas))
                entradas[a.ano_n].append(_ValorFixo(f"{a.vendas:g}"))
            else:
                entradas[a.ano_n].append(ui.input(value=f"{a.vendas:g}").props("dense"))

        # B) Variables
        ui.label("B) Variables")
        for a in filas:
            if hai_custo:
                ui.label(_e(a.variables))
                entradas[a.ano_n].append(_ValorFixo(f"{a.variables:g}"))
            else:
                entradas[a.ano_n].append(ui.input(value=f"{a.variables:g}").props("dense"))

        # C) Fixos
        ui.label("C) Fixos")
        for a in filas:
            entradas[a.ano_n].append(ui.input(value=f"{a.fixos:g}").props("dense"))

        # Ingresos financeiros
        ui.label("Ingresos financeiros")
        for a in filas:
            valor = financeiros.get(a.ano_n, 0)
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

    ui.label("Tesouraría do ano 1").classes("text-subtitle1 text-weight-bold q-mt-md")
    meses_tes = tesouraria(plan)
    ui.echart(opcions_tesouraria(meses_tes)).classes("w-full").style("height: 320px")
    ui.label(
        "Suponse que o financiamento entra no mes 1, as subvencións no mes 12 e o "
        "investimento págase no mes 1 con IVE."
    ).classes("texto-suave text-caption")

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

    ui.label("Memoria complementaria").classes("text-subtitle1 text-weight-bold q-mt-md")
    ui.label(
        "AGADER admítea como documentación complementaria (art. 18.1.p). "
        "Serve tamén para o banco ou para o GDR."
    ).classes("texto-suave text-caption")

    faltas_m = faltas_memoria(plan)
    if faltas_m:
        ui.label("Na memoria falta: " + "; ".join(faltas_m) + ".").classes("etiqueta-aviso")

    campos_lista = {
        "dafo_debilidades",
        "dafo_ameazas",
        "dafo_fortalezas",
        "dafo_oportunidades",
        "argumentos",
        "riscos",
        "permisos",
    }
    entradas_memoria: dict[str, ui.textarea] = {}
    for seccion, campos in SECCIONS_MEMORIA.items():
        with ui.expansion(seccion).classes("w-full"):
            if seccion == "DAFO":
                with ui.grid(columns=2).classes("w-full"):
                    for c in campos:
                        ta = ui.textarea(
                            ETIQUETAS_MEMORIA[c].capitalize(),
                            value=getattr(plan, c) or "",
                        ).classes("w-full").props("autogrow")
                        if c in campos_lista:
                            ta.props('hint="Un punto por liña"')
                        entradas_memoria[c] = ta
            else:
                for c in campos:
                    ta = ui.textarea(
                        ETIQUETAS_MEMORIA[c].capitalize(),
                        value=getattr(plan, c) or "",
                    ).classes("w-full").props("autogrow")
                    if c in campos_lista:
                        ta.props('hint="Un punto por liña"')
                    entradas_memoria[c] = ta

    ui.button("Gardar a memoria", icon="check", on_click=lambda: _accion(
        lambda s, a: actualizar_plan(
            s, a, s.get(PlanEmpresa, plan.id),
            **{c: t.value or None for c, t in entradas_memoria.items()}))).props("outline")

    with ui.expansion("Calendario de 12 meses").classes("w-full"):
        for act in plan.actividades:
            with ui.row().classes("items-center gap-2"):
                ui.label(texto_actividade(act))
                ui.button(icon="delete", on_click=lambda act=act: _accion(
                    lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                        s.get(PlanActividade, act.id)))).props(
                    "flat dense round size=sm color=negative")
        with ui.row().classes("items-end gap-2"):
            meses = list(range(1, 13))
            mes_inicio = ui.select(meses, label="Desde o mes", value=1).classes("w-28")
            mes_fin = ui.select(meses, label="Ata o mes", value=12).classes("w-28")
            act_txt = ui.input("Actividade").classes("w-48")
            resp_txt = ui.input("Responsable").classes("w-36")
            ui.button("Engadir", icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_actividade(
                    s, a, s.get(PlanEmpresa, plan.id),
                    int(mes_inicio.value or 0), int(mes_fin.value or 0),
                    act_txt.value or "", resp_txt.value or None))).props("outline")

    with ui.expansion("Obxectivos e indicadores").classes("w-full"):
        for obx in plan.obxectivos:
            with ui.row().classes("items-center gap-2"):
                ui.label(texto_obxectivo(obx))
                ui.button(icon="delete", on_click=lambda obx=obx: _accion(
                    lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                        s.get(PlanObxectivo, obx.id)))).props(
                    "flat dense round size=sm color=negative")
        with ui.row().classes("items-end gap-2"):
            obx_txt = ui.input("Obxectivo").classes("w-48")
            ind_txt = ui.input("Como se mide").classes("w-48")
            meta_txt = ui.input("Meta").classes("w-32")
            prazo_txt = ui.input("Prazo").classes("w-28")
            ui.button("Engadir", icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_obxectivo(
                    s, a, s.get(PlanEmpresa, plan.id),
                    obx_txt.value or "", ind_txt.value or "",
                    meta_txt.value or None, prazo_txt.value or None))).props("outline")

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

    def descargar_memoria() -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            try:
                datos = xerar_memoria(session, actor, plan.id)
            except OperacionNonPermitidaError as erro:
                ui.notify(str(erro), type="negative")
                return
        descargar_informe(
            datos,
            formato.value or "xlsx",
            f"plan-memoria-{plan.id}",
            "Memoria do plan de empresa",
            "memoria",
        )

    with ui.row().classes("items-center gap-2 q-mt-md"):
        ui.button("Descargar Anexo III e V", icon="download", on_click=descargar)
        ui.button("Descargar a memoria", icon="download", on_click=descargar_memoria).props(
            "outline")


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
            ui.label(
                "Para engadir ofertas, crea as empresas provedoras en Persoas → Contactos."
            ).classes("texto-suave text-caption")
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
