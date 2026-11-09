"""Sección Contas: resumo do ano,
pendente de cobrar e de pagar por persoa, e os outros gastos e ingresos."""

from __future__ import annotations

from datetime import date
from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import _, ngettext
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
from horta.ui.lista_tarxetas import lista_tarxetas
from horta.ui.numeros import euros, formatar_decimal, parsear_data, parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def seccion_cartos(horta_id: int, pode_editar: bool) -> None:
    if not pode_editar:
        ui.label(_("Só quen pode editar a explotación ve os cartos.")).classes("texto-suave")
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
            for titulo, partidas, total in ((_("Ingresos"), resumo.ingresos, resumo.total_ingresos),
                                            (_("Gastos"), resumo.gastos, resumo.total_gastos)):
                with ui.column().classes("tarxeta col gap-1"):
                    ui.label(titulo).classes("text-subtitle1 text-weight-bold")
                    if not partidas:
                        ui.label(_("Nada apuntado neste período")).classes("texto-suave")
                    for nome, valor in partidas.items():
                        with ui.row().classes("w-full justify-between"):
                            ui.label(_(nome))
                            ui.label(euros(valor))
                    with ui.row().classes("w-full justify-between text-weight-bold"):
                        ui.label(_("Total"))
                        ui.label(euros(total))
        with ui.column().classes("tarxeta w-full gap-1 q-mt-md"):
            ui.label(
                _("Resultado ({periodo}): {resultado}").format(
                    periodo=resumo.periodo.nome, resultado=euros(resumo.resultado)
                )
            ).classes("text-subtitle1 text-weight-bold")
            if resumo.custos.man_de_obra_propia:
                ui.label(
                    _(
                        "Sen contar as horas da persoa titular e a familia (non se pagan): "
                        "{resultado}"
                    ).format(resultado=euros(resumo.resultado_sen_man_propia))
                ).classes("texto-suave")
            if resumo.custos.sen_custo:
                ui.label(
                    _(
                        "{n} traballos con horas quedan sen contar: "
                        "falta o custo da hora da persoa ou da máquina (Equipo, Maquinaria)"
                    ).format(n=resumo.custos.sen_custo)
                ).classes("etiqueta-aviso")
            if resumo.vendas_sen_prezo:
                n = resumo.vendas_sen_prezo
                ui.label(
                    ngettext(
                        "1 venda sen prezo queda sen contar nos ingresos (Lotes)",
                        "{n} vendas sen prezo quedan sen contar nos ingresos (Lotes)",
                        n,
                    ).format(n=n)
                ).classes("etiqueta-aviso")

        ui.label(_("Pendente de cobrar e de pagar")).classes(
            "text-subtitle1 text-weight-bold q-mt-md")
        if not saldos:
            ui.label(_("Non hai nada pendente.")).classes("texto-suave")
        for persoa_id, (cobrar, pagar) in sorted(saldos.items(), key=lambda par: -max(par[1])):
            quen = nomes.get(persoa_id or 0)
            if cobrar > 0:
                ui.label(
                    _("Sen persoa: pendente de cobrar {importe}").format(importe=euros(cobrar))
                    if quen is None
                    else _("{quen} débeche {importe}").format(quen=quen, importe=euros(cobrar))
                )
            if pagar > 0:
                ui.label(
                    _("Sen persoa: pendente de pagar {importe}").format(importe=euros(pagar))
                    if quen is None
                    else _("Débeslle a {quen} {importe}").format(quen=quen, importe=euros(pagar))
                )

        with ui.row().classes("w-full items-center justify-between q-mt-md"):
            ui.label(_("Outros gastos e ingresos")).classes("text-subtitle1 text-weight-bold")
            ui.button(_("Novo"), icon="add", on_click=lambda: abrir(None))
        filas: list[dict[str, Any]] = [{
            "id": a.id,
            "data": f"{a.data:%d/%m/%Y}",
            "tipo": _(TIPOS[a.tipo]) if a.tipo in TIPOS else a.tipo,
            "categoria": (
                _(CATEGORIAS[a.categoria]) if a.categoria in CATEGORIAS else a.categoria
            ),
            "concepto": a.concepto,
            "importe": euros(a.importe),
            "quen": nomes.get(a.persoa_id or 0, ""),
            "pago": _("Si") if a.data_pago else _("Pendente"),
        } for a in apuntes]
        columnas = [{"name": c, "label": e, "field": c, "align": "left"} for c, e in (
            ("data", _("Data")), ("tipo", _("Tipo")), ("categoria", _("Categoría")),
            ("concepto", _("Concepto")), ("importe", _("Importe")), ("quen", _("Quen")),
            ("pago", _("Cobrado ou pagado")))]
        ui.table(columns=columnas, rows=filas, row_key="id", selection="single",
                 on_select=lambda e: abrir(e.selection[0]["id"]) if e.selection else None
                 ).classes("w-full so-ordenador").props(
                     f'no-data-label="{_("Aínda non hai apuntes")}" {TEXTOS_TABOA}')
        elementos = [
            (
                int(f["id"]),
                str(f["concepto"] or f["categoria"]),
                " · ".join(str(f[c]) for c in ("data", "importe", "pago") if f.get(c)),
            )
            for f in filas
        ]
        lista_tarxetas(elementos, ao_tocar=abrir, baleiro=_("Aínda non hai apuntes"))

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

        ui.select({k: _(v) for k, v in PERIODOS.items()}, label=_("Resumo por"), value="ano",
                  on_change=lambda e: cambiar_tipo(e.value)).classes("min-w-32")
        escoller = ui.select(opcions(), label=_("Período"),
                             value=estado["periodo"].desde.isoformat(),
                             on_change=lambda e: cambiar_periodo(e.value)).classes("min-w-64")

    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("").classes("text-h6")
        tipo = ui.select(
            {k: _(v) for k, v in TIPOS.items()}, label=_("Tipo"), value="gasto"
        ).classes("w-full")
        categoria = ui.select(
            {k: _(v) for k, v in CATEGORIAS.items()}, label=_("Categoría"), value="outro"
        ).classes("w-full")
        concepto = ui.input(_("Concepto")).classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data(_("Data")).classes(remove="w-full", add="col")
            importe = ui.input(_("Importe (€)")).classes("col")
        persoa = ui.select({}, label=_("A quen ou de quen (opcional)"), clearable=True).classes(
            "w-full")
        albaran = ui.input(_("Factura ou recibo")).classes("w-full")
        pago = CampoPago(_("Cobrado ou pagado"))
        notas = ui.textarea(_("Notas")).classes("w-full")
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
                        raise OperacionNonPermitidaError(_("Indica a data"))
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
                ui.button(_("Gardar"), icon="check", on_click=gardar)
                ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")
            baixa = ui.button(
                _("Dar de baixa"),
                icon="delete",
                on_click=lambda: (
                    confirmar_eliminacion(
                        _("Dar de baixa este apunte?"), dar_de_baixa
                    )
                ),
            ).props("flat color=negative")

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
        titulo.text = _("Editar apunte") if apunte else _("Outro gasto ou ingreso")
        tipo.value = apunte.tipo if apunte else "gasto"
        categoria.value = apunte.categoria if apunte else "outro"
        concepto.value = apunte.concepto if apunte else ""
        data.value = (apunte.data if apunte else date.today()).isoformat()
        importe.value = formatar_decimal(apunte.importe) if apunte else ""
        persoa.value = apunte.persoa_id if apunte else None
        albaran.value = (apunte.albaran_factura or "") if apunte else ""
        pago.poñer(apunte.data_pago if apunte else None, apunte is None)
        notas.value = (apunte.notas or "") if apunte else ""
        baixa.set_visibility(apunte is not None)
        dialogo.open()

    contido()
