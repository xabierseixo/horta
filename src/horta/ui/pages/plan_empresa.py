"""Sección Plan de empresa (paso 16): datos do Anexo III, conta a 5 anos proposta desde o
real, investimento (Anexo V) coas súas ofertas (Anexo VI-A e VI-B), financiamento,
indicadores, o que lle falta, a documentación do art. 18, métricas e seguimento."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _, ngettext
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
    Comparacion,
    Documento,
    MarxeVenda,
    MesTesouraria,
    Revision,
    actualizar_plan,
    ano_de_referencia,
    avisos_plan,
    comparar_recan,
    conta,
    crear_plan,
    documentos_plan,
    engadir_actividade,
    engadir_financiamento,
    engadir_investimento,
    engadir_obxectivo,
    engadir_oferta,
    engadir_venda,
    escenarios,
    faltas_memoria,
    faltas_plan,
    fonte_recan,
    gardar_anos,
    indicadores,
    listar_plans,
    marxes_por_venda,
    meses_de,
    metricas,
    orientacions_recan,
    pct,
    propor_vendas_do_real,
    quitar,
    revision,
    seguimento,
    semaforo,
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
    N_("Xan"), N_("Feb"), N_("Mar"), N_("Abr"), N_("Mai"), N_("Xuñ"),
    N_("Xul"), N_("Ago"), N_("Set"), N_("Out"), N_("Nov"), N_("Dec"),
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


def cor_do_sinal(cor: str) -> str:
    """Mapea a cor do semáforo («verde», «amarelo», «vermello») á cor de NiceGUI."""
    cores = {
        "verde": "positive",
        "amarelo": "warning",
        "vermello": "negative",
    }
    return cores.get(cor, "grey")


def texto_tir(tir: float | None) -> str:
    """TIR en % cun decimal ou «—»."""
    return pct(tir) if tir is not None else "—"


def texto_payback(payback: int | None) -> str:
    """Pay-back en «N anos» ou «—»."""
    if payback is None:
        return "—"
    return ngettext("{n} ano", "{n} anos", payback).format(n=payback)


def texto_valor_unidade(valor: float | None, unidade: str) -> str:
    """Formata un valor coa súa unidade ou «—» se non ten valor."""
    if valor is None:
        return "—"
    if unidade == "%":
        return f"{valor:.1f} %".replace(".", ",")
    return f"{valor:,.0f} {unidade}".replace(",", " ")


def texto_comparacion(c: Comparacion) -> str:
    """Liña de comparación coa media galega."""
    plan_txt = texto_valor_unidade(c.plan, c.unidade)
    media_txt = texto_valor_unidade(c.media, c.unidade)
    return _("{indicador}: o teu plan {plan} · media galega {media}").format(
        indicador=_(c.indicador), plan=plan_txt, media=media_txt
    )


def nota_comparacion(c: Comparacion) -> str | None:
    """Nota explicativa da comparación ou aviso se falta superficie ou UTA."""
    if c.plan is None and c.indicador == "Produción por hectárea":
        return _("Pon a superficie das parcelas para comparar")
    if c.plan is None and c.indicador in ("Produción por UTA", "Resultado por UTA"):
        return _("Pon as UTA mantidas ou creadas (Datos) para comparar")
    return _(c.nota) if c.nota else None


def texto_venda(v: PlanVenda) -> str:
    """Texto para a liña dunha venda prevista en detalle."""
    canle = _(CANLES.get(v.canle, v.canle))
    importe, _custo = vendas_do_ano(v, 1)
    partes = [
        _("{produto} · {canle}: {cantidade} {unidade} a {prezo} € (ano 1: {importe})").format(
            produto=v.produto,
            canle=canle,
            cantidade=_n(v.cantidade),
            unidade=v.unidade,
            prezo=_n(v.prezo),
            importe=_e(importe),
        )
    ]
    if v.custo_unitario is not None:
        partes.append(
            _("custo {custo} €/{unidade}").format(custo=_n(v.custo_unitario), unidade=v.unidade)
        )
    cq = v.crece_cantidade_pct or 0
    cp = v.crece_prezo_pct or 0
    if cq != 0 or cp != 0:
        if cq != 0 and cp != 0:
            x = (
                f"{_n(cq)}"
                if cq == cp
                else _("{cantidade} cantidade, {prezo} prezo").format(
                    cantidade=_n(cq), prezo=_n(cp)
                )
            )
        elif cq != 0:
            x = f"{_n(cq)}"
        else:
            x = f"{_n(cp)}"
        partes.append(_("crece {x} %/ano").format(x=x))
    meses = meses_de(v.meses)
    if meses != list(range(1, 13)):
        partes.append(_("meses {meses}").format(meses=", ".join(str(m) for m in meses)))
    return " · ".join(partes)


def texto_marxe(m: MarxeVenda) -> str:
    """Texto para a liña da marxe por venda no ano 1."""
    canle = _(CANLES.get(m.canle, m.canle))
    pct = f"{_n(m.marxe_pct)} %" if m.marxe_pct is not None else "—"
    return _(
        "{produto} · {canle}: vende {importe}, custa {custo}, deixa {marxe} ({pct})"
    ).format(
        produto=m.produto,
        canle=canle,
        importe=_e(m.importe),
        custo=_e(m.custo),
        marxe=_e(m.marxe),
        pct=pct,
    )


def opcions_tesouraria(meses: list[MesTesouraria]) -> dict[str, Any]:
    """Opcións para o gráfico de tesouraría mes a mes do ano 1."""
    return {
        "tooltip": {"trigger": "axis"},
        "legend": {"top": 0},
        "grid": {"left": 50, "right": 50, "top": 40, "bottom": 30},
        "xAxis": {"type": "category", "data": [_(m) for m in MESES_TESOURARIA]},
        "yAxis": {"type": "value"},
        "series": [
            {"name": _("Cobros"), "type": "bar", "data": [m.cobros for m in meses]},
            {"name": _("Pagos"), "type": "bar", "data": [m.pagos for m in meses]},
            {"name": _("Saldo acumulado"), "type": "line", "data": [m.saldo for m in meses]},
        ],
    }


def texto_actividade(a: PlanActividade) -> str:
    """Texto para a liña dunha actividade do calendario."""
    rango = (
        _("Mes {mes}").format(mes=a.mes_inicio)
        if a.mes_inicio == a.mes_fin
        else _("Mes {inicio}–{fin}").format(inicio=a.mes_inicio, fin=a.mes_fin)
    )
    responsable = getattr(a, "responsable", None)
    resp = f" · {responsable}" if responsable else ""
    return f"{rango}: {a.actividade}{resp}"


def texto_obxectivo(o: PlanObxectivo) -> str:
    """Texto para a liña dun obxectivo co seu indicador."""
    res = _("{obxectivo} — mídese con {indicador}").format(
        obxectivo=o.obxectivo, indicador=o.indicador
    )
    meta = getattr(o, "meta", None)
    if meta:
        res += _(" · meta: {meta}").format(meta=meta)
    prazo = getattr(o, "prazo", None)
    if prazo:
        res += _(" · prazo: {prazo}").format(prazo=prazo)
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
        ui.label(_("Só quen pode editar a explotación ve o plan de empresa.")).classes(
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
        revs = {p.id: revision(session, actor, p) for p in plans}
        comps = {p.id: comparar_recan(session, actor, p) for p in plans}
        provedores = con_papel(session, horta_id, "provedor")
        nomes = {p.id: nome_completo(p) for p in
                 session.query(Persoa).filter_by(horta_id=horta_id)}

    with ui.row().classes("items-end gap-2"):
        titulo = ui.input(_("Título do novo plan")).classes("w-64")
        ano1 = ui.input(_("Ano 1"), value=str(date.today().year + 1)).classes("w-24")
        ui.button(_("Novo plan"), icon="add", on_click=lambda: _accion(
            lambda s, a: crear_plan(s, a, horta_id, titulo.value or "",
                                    int(parsear_decimal(ano1.value) or date.today().year))))
    referencia = (
        _("ao ano pasado")
        if ano_real < date.today().year
        else _("ao que levas de {ano}").format(ano=ano_real)
    )
    ui.label(
        _("Os 5 anos propóñense iguais {referencia} en Contas; cámbiaos na conta.").format(
            referencia=referencia
        )
    ).classes("texto-suave text-caption")

    for plan in plans:
        with ui.expansion(
            _("{titulo} · ano 1: {ano}").format(titulo=plan.titulo, ano=plan.ano_inicio),
            icon="business_center",
        ).classes("w-full tarxeta q-mt-md"):
            _plan(plan, segue[plan.id], faltas[plan.id], docs[plan.id],
                  {p.id: nome_completo(p) for p in provedores}, nomes,
                  revs[plan.id], comps[plan.id])

    with ui.expansion(
        _("Métricas da explotación en {ano}").format(ano=ano_real), icon="insights"
    ).classes("w-full tarxeta q-mt-md"):
        for nome, valores, unidade in ((_("Rendemento"), met.rendemento, " kg/ha"),
                                       (_("Prezo medio de venda"), met.prezo_medio, " €"),
                                       (_("Refugo"), met.refugo_pct, " %")):
            ui.label(nome).classes("text-weight-bold")
            if not valores:
                ui.label(_("Sen datos")).classes("texto-suave")
            for clave, valor in valores.items():
                ui.label(f"{clave}: {valor:g}{unidade}")
        ui.label(
            _("Horas de traballo: {horas:g} ({uta:g} UTA)").format(
                horas=met.horas, uta=met.uta
            )
        )
        punto_morto_txt = (
            _e(met.punto_morto) if met.punto_morto is not None else _("sen datos")
        )
        ui.label(
            _("Punto morto (vendas para cubrir custos): {pm}").format(pm=punto_morto_txt)
        )


def _plan(plan: PlanEmpresa, segue: list, faltas: list[str], docs: list[Documento],
          provedores: dict[int, str], nomes: dict[int, str],
          rev: Revision | None = None, comps: list[Comparacion] | None = None) -> None:
    ind = indicadores(plan)
    if faltas:
        ui.label(
            _("Para presentalo falta: {faltas}.").format(
                faltas="; ".join(_(f) for f in faltas)
            )
        ).classes("etiqueta-aviso")
    for aviso in avisos_plan(plan):
        ui.label(_(aviso)).classes("etiqueta-aviso")
    with ui.row().classes("gap-6"):
        ui.label(
            _("Investimento: {inv} (con IVE {con_iva})").format(
                inv=_e(ind.investimento), con_iva=_e(ind.investimento_con_iva)
            )
        )
        ui.label(_("VAN: {van}").format(van=_e(ind.van)))
        ui.label(_("TIR: {tir}").format(tir=texto_tir(ind.tir)))
        ui.label(_("Pay-back: {pb}").format(pb=texto_payback(ind.payback)))

    ui.label(_("Como vai o plan")).classes("text-subtitle1 text-weight-bold q-mt-md")
    for s in semaforo(plan):
        with ui.row().classes("items-center gap-2"):
            ui.icon("circle", color=cor_do_sinal(s.cor))
            ui.label(f"{_(s.nome)}: {_(s.texto)}")

    with ui.expansion(_("Que se pode afirmar e que falta probar")).classes("w-full"):
        if rev and rev.afirmable:
            ui.label(_("Pódese afirmar")).classes("text-weight-bold")
            for texto in rev.afirmable:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("check", color="positive")
                    ui.label(_(texto))
        if rev and rev.falta_probar:
            ui.label(_("Falta probar")).classes("text-weight-bold")
            for texto in rev.falta_probar:
                with ui.row().classes("items-center gap-2"):
                    ui.icon("help_outline", color="warning")
                    ui.label(_(texto))

    ui.label(_("Datos (Anexo III)")).classes("text-subtitle1 text-weight-bold q-mt-md")
    tipoloxia = ui.select(
        {k: _(t.texto) for k, t in TIPOLOXIAS.items()},
        label=_("Tipoloxía"),
        value=plan.tipoloxia,
        clearable=True,
    ).classes("w-full")
    if plan.tipoloxia in TIPOLOXIAS:
        ui.label(
            _("Axuda: {axuda}").format(axuda=_(TIPOLOXIAS[plan.tipoloxia].axuda))
        ).classes("texto-suave text-caption")
    with ui.row().classes("gap-2"):
        proxecto = {
            c: ui.input(_(e), value=str(getattr(plan, c) or "")).classes("w-40")
            for c, e in (
                ("expediente", "Nº de expediente"),
                ("anualidade", "Anualidade"),
                ("submedida", "Submedida"),
                ("gdr", "Grupo (GDR)"),
            )
        }
    ui.label(_("O expediente, a anualidade e a submedida dáos o GDR.")).classes(
        "texto-suave text-caption"
    )
    with ui.row().classes("items-end gap-2"):
        nova = ui.checkbox(_("Empresa nova"), value=plan.empresa_nova)
        cnae = ui.input(_("CNAE"), value=plan.cnae or "").classes("w-32")
        participada = ui.checkbox(_("Participa ou está participada nun 25 % ou máis"),
                                  value=plan.participada)
    with ui.row().classes("gap-2"):
        empresa = {c: ui.input(_(e), value="" if getattr(plan, c) is None
                               else f"{getattr(plan, c):g}").classes("w-36")
                   for c, e in (("traballadores", "Nº de persoas traballadoras"),
                                ("facturacion", "Facturación (€)"), ("balance", "Balance (€)"))}
    recuperable = ui.checkbox(
        _("O IVE é recuperable (se non o é, o investimento conta con IVE)"),
                      value=plan.iva_recuperable)
    textos = {c: ui.textarea(_(e), value=getattr(plan, c) or "").classes("w-full")
              for c, e in (("descricion", "1. Descrición, obxectivos e finalidade"),
                           ("proceso", "2. Proceso e medios humanos e materiais"),
                           ("formacion", "4. Formación do promotor"))}
    with ui.row().classes("gap-2"):
        utas = {c: ui.input(_(e), value=f"{getattr(plan, c):g}").classes("w-28")
                for c, e in (("uta_mantidas", "UTA mantidas"), ("uta_creadas", "UTA creadas"),
                             ("uta_mulleres", "…mulleres"), ("uta_mozas", "…mozas"),
                             ("uta_maiores", "…maiores"),
                             ("uta_discapacidade", "…discapacidade"),
                             ("uta_outros", "…outros"))}
    taxa = ui.input(
        _("Taxa para o VAN (p.ex. 0,03)"), value=f"{plan.taxa_desconto:g}"
    ).classes("w-48")
    ui.label(_("Declaracións do Anexo VI-B")).classes("text-weight-medium")
    declaracions = {c: ui.checkbox(_(e), value=getattr(plan, c))
                    for c, e in (
                        ("ofertas_autenticas", "As ofertas son auténticas"),
                        ("sen_vinculo_promotor",
                         "Non hai vinculación coas empresas provedoras"),
                        ("sen_vinculo_entre_provedores",
                         "As empresas provedoras de cada gasto non están vinculadas entre elas"),
                    )}
    ui.button(_("Gardar os datos"), icon="check", on_click=lambda: _accion(
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

    ui.label(_("Vendas en detalle")).classes("text-subtitle1 text-weight-bold q-mt-md")
    ui.label(
        _(
            "Se engades as vendas por produto e canle, a conta calcula con elas as vendas de cada "
            "ano (e os custos variables, se pos o custo por unidade)."
        )
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
        v_produto = ui.input(_("Produto")).classes("w-40")
        v_unidade = ui.input(_("Unidade"), value="kg").classes("w-20")
        v_canle = ui.select(
            {k: _(v) for k, v in CANLES.items()},
            label=_("Canle"),
            value="explotacion",
        ).classes("w-48")
        v_cantidade = ui.input(_("Cantidade (ano 1)")).classes("w-32")
        v_prezo = ui.input(_("Prezo €/unidade")).classes("w-28")
        v_custo = ui.input(_("Custo €/unidade")).classes("w-28")
        v_crece_cant = ui.input(_("Crece cantidade %/ano")).classes("w-36")
        v_crece_prezo = ui.input(_("Crece prezo %/ano")).classes("w-32")
        v_meses = ui.select(
            {m: str(m) for m in range(1, 13)},
            label=_("Meses de venda"),
            multiple=True,
        ).classes("w-40")
        ui.button(
            _("Engadir"),
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
                    ui.notify(
                        ngettext(
                            "Engadiuse {n} venda",
                            "Engadíronse {n} vendas",
                            n,
                        ).format(n=n)
                    )
                    ui.navigate.reload()
                else:
                    ui.notify(_("Non hai vendas con importe ese ano"))

        ui.button(_("Propoñer desde as vendas reais"), on_click=propor_vendas).props("outline")
    else:
        ui.label(_("Marxe por produto e canle (ano 1)")).classes("text-weight-bold q-mt-sm")
        for m in marxes_por_venda(plan):
            ui.label(texto_marxe(m))

    ui.label(_("Conta de explotación (6)")).classes("text-subtitle1 text-weight-bold q-mt-md")
    filas = conta(plan)
    entradas: dict[int, list[Any]] = {a.ano_n: [] for a in filas}
    hai_detalle = bool(plan.vendas_detalle)
    hai_custo = hai_detalle and any(v.custo_unitario is not None for v in plan.vendas_detalle)
    with ui.grid(columns=6).classes("w-full gap-1 items-center"):
        for texto in ("", *(_("Ano {n} ({ano})").format(n=a.ano_n, ano=a.ano) for a in filas)):
            ui.label(texto).classes("text-weight-bold text-caption")
        financeiros = {a.ano_n: a.ingresos_financeiros for a in plan.anos}

        # A) Vendas
        ui.label(_("A) Vendas"))
        for a in filas:
            if hai_detalle:
                ui.label(_e(a.vendas))
                entradas[a.ano_n].append(_ValorFixo(f"{a.vendas:g}"))
            else:
                entradas[a.ano_n].append(ui.input(value=f"{a.vendas:g}").props("dense"))

        # B) Variables
        ui.label(_("B) Variables"))
        for a in filas:
            if hai_custo:
                ui.label(_e(a.variables))
                entradas[a.ano_n].append(_ValorFixo(f"{a.variables:g}"))
            else:
                entradas[a.ano_n].append(ui.input(value=f"{a.variables:g}").props("dense"))

        # C) Fixos
        ui.label(_("C) Fixos"))
        for a in filas:
            entradas[a.ano_n].append(ui.input(value=f"{a.fixos:g}").props("dense"))

        # Ingresos financeiros
        ui.label(_("Ingresos financeiros"))
        for a in filas:
            valor = financeiros.get(a.ano_n, 0)
            entradas[a.ano_n].append(ui.input(value=f"{valor:g}").props("dense"))

        for nome, campo in ((N_("D) Amortizacións"), "amortizacions"), (N_("E) Marxe"), "marxe"),
                            (N_("F) Financeiro"), "financeiro"),
                            (N_("G) Beneficio"), "beneficio")):
            ui.label(_(nome))
            for a in filas:
                ui.label(_e(getattr(a, campo)))

    def gardar_conta(session: Any, actor: Any) -> None:
        valores = {n: (parsear_decimal(v.value) or 0, parsear_decimal(b.value) or 0,
                       parsear_decimal(c.value) or 0, parsear_decimal(f.value) or 0)
                   for n, (v, b, c, f) in entradas.items()}
        gardar_anos(session, actor, session.get(PlanEmpresa, plan.id), valores)

    ui.button(_("Gardar a conta"), icon="check", on_click=lambda: _accion(gardar_conta)).props(
        "outline")

    ui.label(_("Escenarios")).classes("text-subtitle1 text-weight-bold q-mt-md")
    with ui.row().classes("items-end gap-2"):
        esc_pct = ui.input(
            _("Variación das vendas nos escenarios (%)"),
            value=f"{plan.escenario_pct:g}" if plan.escenario_pct is not None else "20",
        ).classes("w-64")
        ui.button(
            _("Gardar"),
            icon="check",
            on_click=lambda: _accion(
                lambda s, a: actualizar_plan(
                    s, a, s.get(PlanEmpresa, plan.id),
                    escenario_pct=parsear_decimal(esc_pct.value),
                )
            ),
        ).props("outline")

    esc_lista = escenarios(plan)
    with ui.grid(columns=4).classes("w-full gap-1 items-center"):
        for texto in ("", _("Pesimista"), _("Normal"), _("Optimista")):
            ui.label(texto).classes("text-weight-bold text-caption")

        ui.label(_("Vendas do ano 1"))
        for e in esc_lista:
            ui.label(_e(e.vendas_ano1))

        ui.label(_("Beneficio do ano 1"))
        for e in esc_lista:
            ui.label(_e(e.beneficio_ano1))

        ui.label(_("VAN"))
        for e in esc_lista:
            ui.label(_e(e.van))

        ui.label(_("TIR"))
        for e in esc_lista:
            ui.label(texto_tir(e.tir))

        ui.label(_("Pay-back"))
        for e in esc_lista:
            ui.label(texto_payback(e.payback))

    ui.label(_("Os custos quedan iguais en todos os escenarios.")).classes(
        "texto-suave text-caption"
    )

    ui.label(_("Comparación coa media galega")).classes("text-subtitle1 text-weight-bold q-mt-md")
    with ui.row().classes("items-end gap-2"):
        ote = ui.select(
            orientacions_recan(),
            label=_("Tipo de explotación (RECAN)"),
            value=plan.ote_recan,
            clearable=True,
        ).classes("w-72")
        ui.button(
            _("Gardar"),
            icon="check",
            on_click=lambda: _accion(
                lambda s, a: actualizar_plan(
                    s, a, s.get(PlanEmpresa, plan.id), ote_recan=ote.value or None
                )
            ),
        ).props("outline")

    if comps:
        for comp in comps:
            ui.label(texto_comparacion(comp))
            nota = nota_comparacion(comp)
            if nota:
                ui.label(nota).classes("texto-suave text-caption")

    ui.label(_("Fonte: {fonte}").format(fonte=fonte_recan())).classes("texto-suave text-caption")

    ui.label(_("Tesouraría do ano 1")).classes("text-subtitle1 text-weight-bold q-mt-md")
    meses_tes = tesouraria(plan)
    ui.echart(opcions_tesouraria(meses_tes)).classes("w-full").style("height: 320px")
    ui.label(_(
        "Suponse que o financiamento entra no mes 1, as subvencións no mes 12 e o "
        "investimento págase no mes 1 con IVE."
    )).classes("texto-suave text-caption")

    ui.label(_("Investimento (Anexo V)")).classes("text-subtitle1 text-weight-bold q-mt-md")
    for i in sorted(plan.investimentos, key=lambda i: i.partida):
        with ui.row().classes("items-center gap-2"):
            ui.label(_("{partida} · {concepto}: {importe} + {iva} % IVE").format(
                partida=_(PARTIDAS[i.partida]), concepto=i.concepto,
                importe=_e(i.importe_sen_iva), iva=f"{i.iva_pct:g}"))
            ui.button(icon="delete", on_click=lambda i=i: _accion(
                lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                    s.get(PlanInvestimento, i.id)))).props(
                "flat dense round size=sm color=negative")
        _ofertas(plan, i, provedores, nomes)
    with ui.row().classes("items-end gap-2"):
        partida = ui.select(
            {k: _(v) for k, v in PARTIDAS.items()}, label=_("Partida"), value="3"
        ).classes("w-56")
        concepto = ui.input(_("Concepto")).classes("w-48")
        importe = ui.input(_("Sen IVE (€)")).classes("w-28")
        iva = ui.input(_("IVE %"), value="21").classes("w-20")
        vida = ui.input(_("Vida útil (anos)"), value="10").classes("w-28")
        motivo = ui.input(_("Se non hai tres ofertas, por que")).classes("w-64")
        ui.button(_("Engadir"), icon="add", on_click=lambda: _accion(
            lambda s, a: engadir_investimento(
                s, a, s.get(PlanEmpresa, plan.id), partida.value, concepto.value or "",
                parsear_decimal(importe.value) or 0, parsear_decimal(iva.value) or 0,
                int(parsear_decimal(vida.value) or 0), motivo.value or None
            ))).props("outline")

    ui.label(_("Financiamento (5)")).classes("text-subtitle1 text-weight-bold q-mt-md")
    for f in plan.financiamento:
        with ui.row().classes("items-center gap-2"):
            extra = (
                _(" · {xuro} % a {anos} anos").format(xuro=f"{f.xuro_pct:g}", anos=f.anos)
                if f.tipo == "prestamo" else ""
            )
            ui.label(f"{_(FONTES[f.tipo])}: {_e(f.importe)}{extra}")
            ui.button(icon="delete", on_click=lambda f=f: _accion(
                lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                    s.get(PlanFinanciamento, f.id)))).props(
                "flat dense round size=sm color=negative")
    with ui.row().classes("items-end gap-2"):
        fonte = ui.select(
            {k: _(v) for k, v in FONTES.items()}, label=_("Fonte"), value="propios"
        ).classes("w-48")
        canto = ui.input(_("Importe (€)")).classes("w-28")
        xuro = ui.input(_("Xuro % (préstamo)")).classes("w-32")
        anos = ui.input(_("Anos (préstamo)")).classes("w-28")
        ui.button(_("Engadir"), icon="add", on_click=lambda: _accion(
            lambda s, a: engadir_financiamento(
                s, a, s.get(PlanEmpresa, plan.id), fonte.value,
                parsear_decimal(canto.value) or 0, parsear_decimal(xuro.value),
                int(parsear_decimal(anos.value) or 0) or None))).props("outline")

    ui.label(_("Documentación (art. 18)")).classes("text-subtitle1 text-weight-bold q-mt-md")
    for doc in docs:
        with ui.row().classes("items-center gap-2 no-wrap"):
            ui.icon("check_circle" if doc.da_app else "upload_file").classes(
                "text-positive" if doc.da_app else "text-grey")
            ui.label(f"{doc.letra}) {doc.texto}" + ("" if doc.da_app else _(" · achégao ti"))
                     ).classes("text-body2")

    ui.label(_("Memoria complementaria")).classes("text-subtitle1 text-weight-bold q-mt-md")
    ui.label(_(
        "AGADER admítea como documentación complementaria (art. 18.1.p). "
        "Serve tamén para o banco ou para o GDR."
    )).classes("texto-suave text-caption")

    faltas_m = faltas_memoria(plan)
    if faltas_m:
        ui.label(
            _("Na memoria falta: {faltas}.").format(faltas="; ".join(_(f) for f in faltas_m))
        ).classes("etiqueta-aviso")

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
        with ui.expansion(_(seccion)).classes("w-full"):
            if seccion == N_("DAFO"):
                with ui.grid(columns=2).classes("w-full"):
                    for c in campos:
                        ta = ui.textarea(
                            _(ETIQUETAS_MEMORIA[c]).capitalize(),
                            value=getattr(plan, c) or "",
                        ).classes("w-full").props("autogrow")
                        if c in campos_lista:
                            ta.props(f'hint="{_("Un punto por liña")}"')
                        entradas_memoria[c] = ta
            else:
                for c in campos:
                    ta = ui.textarea(
                        _(ETIQUETAS_MEMORIA[c]).capitalize(),
                        value=getattr(plan, c) or "",
                    ).classes("w-full").props("autogrow")
                    if c in campos_lista:
                        ta.props(f'hint="{_("Un punto por liña")}"')
                    entradas_memoria[c] = ta

    ui.button(_("Gardar a memoria"), icon="check", on_click=lambda: _accion(
        lambda s, a: actualizar_plan(
            s, a, s.get(PlanEmpresa, plan.id),
            **{c: t.value or None for c, t in entradas_memoria.items()}))).props("outline")

    with ui.expansion(_("Calendario de 12 meses")).classes("w-full"):
        for act in plan.actividades:
            with ui.row().classes("items-center gap-2"):
                ui.label(texto_actividade(act))
                ui.button(icon="delete", on_click=lambda act=act: _accion(
                    lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                        s.get(PlanActividade, act.id)))).props(
                    "flat dense round size=sm color=negative")
        with ui.row().classes("items-end gap-2"):
            meses = list(range(1, 13))
            mes_inicio = ui.select(meses, label=_("Desde o mes"), value=1).classes("w-28")
            mes_fin = ui.select(meses, label=_("Ata o mes"), value=12).classes("w-28")
            act_txt = ui.input(_("Actividade")).classes("w-48")
            resp_txt = ui.input(_("Responsable")).classes("w-36")
            ui.button(_("Engadir"), icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_actividade(
                    s, a, s.get(PlanEmpresa, plan.id),
                    int(mes_inicio.value or 0), int(mes_fin.value or 0),
                    act_txt.value or "", resp_txt.value or None))).props("outline")

    with ui.expansion(_("Obxectivos e indicadores")).classes("w-full"):
        for obx in plan.obxectivos:
            with ui.row().classes("items-center gap-2"):
                ui.label(texto_obxectivo(obx))
                ui.button(icon="delete", on_click=lambda obx=obx: _accion(
                    lambda s, a: quitar(s, a, s.get(PlanEmpresa, plan.id),
                                        s.get(PlanObxectivo, obx.id)))).props(
                    "flat dense round size=sm color=negative")
        with ui.row().classes("items-end gap-2"):
            obx_txt = ui.input(_("Obxectivo")).classes("w-48")
            ind_txt = ui.input(_("Como se mide")).classes("w-48")
            meta_txt = ui.input(_("Meta")).classes("w-32")
            prazo_txt = ui.input(_("Prazo")).classes("w-28")
            ui.button(_("Engadir"), icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_obxectivo(
                    s, a, s.get(PlanEmpresa, plan.id),
                    obx_txt.value or "", ind_txt.value or "",
                    meta_txt.value or None, prazo_txt.value or None))).props("outline")

    if segue:
        ui.label(_("Seguimento: previsto e real")).classes(
            "text-subtitle1 text-weight-bold q-mt-md"
        )
        for s in segue:
            ui.label(_(
                "{ano}: vendas {pv} previstas, {rv} reais · marxe {pm} prevista, {rm} real"
            ).format(ano=s.ano, pv=_e(s.previsto_vendas), rv=_e(s.real_vendas),
                     pm=_e(s.previsto_marxe), rm=_e(s.real_marxe)))

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
            _("Plan de empresa"),
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
            _("Memoria do plan de empresa"),
            "memoria",
        )

    with ui.row().classes("items-center gap-2 q-mt-md"):
        ui.button(_("Descargar Anexo III e V"), icon="download", on_click=descargar)
        ui.button(_("Descargar a memoria"), icon="download", on_click=descargar_memoria).props(
            "outline")


def _ofertas(plan: PlanEmpresa, investimento: PlanInvestimento, provedores: dict[int, str],
             nomes: dict[int, str]) -> None:
    """As ofertas dun concepto (Anexo VI-A) e o formulario para engadir outra."""
    with ui.column().classes("q-ml-lg gap-1"):
        if investimento.motivo_sen_ofertas:
            ui.label(
                _("Sen tres ofertas: {motivo}").format(motivo=investimento.motivo_sen_ofertas)
            ).classes(
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
            ui.label(_(
                "Para engadir ofertas, crea as empresas provedoras en Persoas → Contactos."
            )).classes("texto-suave text-caption")
            return
        with ui.row().classes("items-end gap-2"):
            provedor = ui.select(provedores, label=_("Provedor")).classes("w-48")
            importe = ui.input(_("Sen IVE (€)")).classes("w-28")
            elixida = ui.checkbox(_("Elixida"))
            criterio = ui.input(_("Criterio")).classes("w-36")
            xustificacion = ui.input(_("Por que non a máis barata")).classes("w-48")
            ui.button(_("Oferta"), icon="add", on_click=lambda: _accion(
                lambda s, a: engadir_oferta(
                    s, a, s.get(PlanEmpresa, plan.id), s.get(PlanInvestimento,
                                                             investimento.id),
                    provedor.value, parsear_decimal(importe.value) or 0, elixida.value,
                    criterio.value or None, xustificacion.value or None))).props(
                "outline dense")
