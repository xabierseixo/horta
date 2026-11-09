"""Tratamentos de postcolleita, almacén e transporte (caderno 3.3–3.5), baixo os tratamentos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _
from horta.models.tarefa import Tarefa
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.models.tratamento_instalacion import TIPOS_INSTALACION, TratamentoInstalacion
from horta.services.catalogos import buscar_cultivos, describir, valores_vixentes
from horta.services.errors import OperacionNonPermitidaError
from horta.services.instalacions import listar_instalacions
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_quen
from horta.services.produtos import listar_entradas, listar_produtos
from horta.services.textos_catalogo import texto_catalogo
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    actualizar_tratamento_instalacion,
    crear_tratamento_instalacion,
    dar_de_baixa_tratamento_instalacion,
    listar_tratamentos_instalacion,
)
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_ETIQUETA_PROBLEMA = {
    "enfermidade": N_("Enfermidade"),
    "praga": N_("Praga"),
    "mala_herba": N_("Mala herba"),
    "regulador": N_("Regulador / outros"),
}
_QUE = {
    "postcolleita": N_("Produto vexetal tratado"),
    "local": N_("Local (tipo e enderezo)"),
    "transporte": N_("Vehículo (tipo, modelo e matrícula)"),
}
_CANTIDADE = {
    "postcolleita": N_("Cantidade de produto tratado (t)"),
    "local": N_("Volume tratado (m³)"),
    "transporte": N_("Volume tratado (m³)"),
}


def seccion_tratamentos_instalacion(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        tratamentos = listar_tratamentos_instalacion(session, actor, horta_id)
        filas = [{
            "id": t.id, "data": f"{t.data:%d/%m/%Y}",
            "tipo": _(TIPOS_INSTALACION[t.tipo]) if t.tipo in TIPOS_INSTALACION else t.tipo,
            "que": t.obxecto,
            "problema": describir(session, t.problema_tipo, t.problema_codigo)
            if t.problema_tipo and t.problema_codigo else "",
            "produto": t.nome_comercial or t.materia_activa or "",
        } for t in tratamentos]

    ui.label(_("Postcolleita, almacéns e transporte")).classes("text-h6 q-mt-lg")
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", _("Data")), ("tipo", _("Tipo")), ("que", _("Que se tratou")),
            ("problema", _("Problema")), ("produto", _("Produto")))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="{_("Ningún tratamento destes")}" {TEXTOS_TABOA}')

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    tarxetas_da_taboa(taboa, "data", ["tipo", "que"], accions_tarxeta)

    if not pode_editar:
        return

    abrir = dialogo_tratamento_instalacion(horta_id)

    def escollido() -> TratamentoInstalacion | None:
        if not taboa.selected:
            ui.notify(_("Escolle primeiro un tratamento na táboa"), type="warning")
            return None
        return next(t for t in tratamentos if t.id == taboa.selected[0]["id"])

    def editar() -> None:
        t = escollido()
        if t is not None:
            abrir(t)

    def dar_de_baixa() -> None:
        t = escollido()
        if t is None:
            return
        tratamento_id = t.id

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                x = session.get(TratamentoInstalacion, tratamento_id)
                if actor_actual is None or x is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_tratamento_instalacion(
                    session, actor_actual, x))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            _("Dar de baixa este tratamento? Non se borra: consérvase no histórico."), confirmar)

    accions_tarxeta += [(_("Editar"), "edit", editar),
                        (_("Dar de baixa"), "archive", dar_de_baixa)]

    with ui.row():
        ui.button(_("Apuntar postcolleita, almacén ou transporte"), icon="add",
                  on_click=lambda: abrir(None))
        with ui.row().classes("so-ordenador"):
            ui.button(_("Editar"), icon="edit", on_click=editar).props("outline")
            ui.button(_("Dar de baixa"), icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_tratamento_instalacion(
    horta_id: int,
) -> Callable[[TratamentoInstalacion | None], None]:
    """Constrúe o diálogo do tratamento de instalacións e devolve a función que o abre."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda _x: None
        problemas = {t: {v.codigo: v.descricion for v in valores_vixentes(session, t)}
                     for t in TIPOS_PROBLEMA}
        xustificacions = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                          for v in valores_vixentes(session, "xustificacion")}
        tipos_produto = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                         for v in valores_vixentes(session, "tipo_produto")}
        unidades = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                    for v in valores_vixentes(session, "unidade_medida")}
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
        instalacions = {i.id: i.nome for i in listar_instalacions(session, actor, horta_id)}
        produtos = {c.codigo: nome for c, nome in buscar_cultivos(session, "", 2000)}
        eficacias = {v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
                     for v in valores_vixentes(session, "eficacia")}
        # Produtos do almacén e as súas compras, para descontar o que se usa (Z8)
        do_almacen = [p for p in listar_produtos(session, actor, horta_id)
                      if p.tipo in ("fitosanitario", "outro")]
        compras: dict[int, dict[int, str]] = {p.id: {} for p in do_almacen}
        for e in listar_entradas(session, actor, horta_id):
            if e.produto_id in compras and not e.baixa:
                compras[e.produto_id][e.id] = f"{e.data:%d/%m/%Y}" + (
                    f" · {e.lote_provedor}" if e.lote_provedor else "")

    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label(_("Apuntar tratamento")).classes("text-h6")
        tipo = ui.select({k: _(v) for k, v in TIPOS_INSTALACION.items()},
                         value="postcolleita", label=_("Que tipo")).classes("w-full")
        data = campo_data(_("Data"), date.today().isoformat())
        persoa = ui.select(persoas, label=_("Quen o fixo")).classes("w-full")
        obxecto = ui.input(_(_QUE["postcolleita"])).classes("w-full")
        catastro = ui.input(_("Referencia catastral do local")).classes("w-full")
        catastro.bind_visibility_from(tipo, "value", backward=lambda v: v == "local")
        instalacion = ui.select(instalacions, label=_("Instalación"), clearable=True).classes(
            "w-full")
        instalacion.bind_visibility_from(tipo, "value", backward=lambda v: v == "local")
        produto_vexetal = ui.select(produtos, label=_("Produto vexetal (lista oficial)"),
                                    with_input=True, clearable=True).classes("w-full")
        produto_vexetal.bind_visibility_from(tipo, "value",
                                             backward=lambda v: v == "postcolleita")
        cantidade_tratada = ui.input(_(_CANTIDADE["postcolleita"])).classes("w-full")

        def cambiar_tipo() -> None:
            obxecto.props(f'label="{_(_QUE[tipo.value])}"')
            cantidade_tratada.props(f'label="{_(_CANTIDADE[tipo.value])}"')

        tipo.on_value_change(cambiar_tipo)
        tipo_problema = ui.select({k: _(v) for k, v in _ETIQUETA_PROBLEMA.items()}, value="praga",
                                  label=_("Tipo de problema")).classes("w-full")
        problema = ui.select(problemas["praga"], label=_("Problema"), with_input=True,
                             clearable=True).classes("w-full")
        tipo_problema.on_value_change(
            lambda e: problema.set_options(problemas[e.value], value=None))
        xustificacion = ui.select(xustificacions, label=_("Xustificación"),
                                  clearable=True).classes("w-full")
        tipo_produto = ui.select(tipos_produto, label=_("Tipo de produto"),
                                 clearable=True).classes("w-full")
        produto = ui.select({p.id: p.nome for p in do_almacen},
                            label=_("Produto do almacén (para descontalo)"), with_input=True,
                            clearable=True).classes("w-full")
        compra = ui.select({}, label=_("De que compra"), clearable=True).classes("w-full")
        compra.bind_visibility_from(produto, "value", backward=lambda v: v is not None)
        nome_comercial = ui.input(_("Nome comercial")).classes("w-full")
        num_rexistro = ui.input(_("Nº de rexistro")).classes("w-full")
        por_id = {p.id: p for p in do_almacen}

        def cambiar_produto() -> None:
            compra.set_options(compras.get(produto.value, {}), value=None)
            escollido = por_id.get(produto.value)
            if escollido is not None:
                nome_comercial.value = escollido.nome
                num_rexistro.value = escollido.num_rexistro or num_rexistro.value

        produto.on_value_change(cambiar_produto)
        materia_activa = ui.input(_("Materia activa")).classes("w-full")
        with ui.row().classes("w-full no-wrap"):
            cantidade = ui.input(_("Cantidade utilizada")).classes("col")
            unidade = ui.select(unidades, label=_("Unidade"), with_input=True).classes("col")
        eficacia = ui.select(eficacias, label=_("Eficacia"), clearable=True).classes("w-full")
        horas = ui.input(_("Horas de traballo")).classes("w-full")
        maquina = ui.select(maquinas, label=_("Máquina"), clearable=True).classes("w-full")
        notas = ui.textarea(_("Notas")).classes("w-full")

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if dia is None:
                        raise OperacionNonPermitidaError(_("Indica a data"))
                    datos = DatosTratamentoInstalacion(
                        tipo=tipo.value, data=dia, obxecto=obxecto.value or "",
                        referencia_catastral=catastro.value if tipo.value == "local" else None,
                        problema_tipo=tipo_problema.value if problema.value else None,
                        problema_codigo=problema.value, xustificacion=xustificacion.value,
                        cantidade_tratada=parsear_decimal(cantidade_tratada.value),
                        tipo_produto=tipo_produto.value,
                        nome_comercial=nome_comercial.value or None,
                        num_rexistro=num_rexistro.value or None,
                        materia_activa=materia_activa.value or None,
                        cantidade_utilizada=parsear_decimal(cantidade.value),
                        unidade=unidade.value, produto_id=produto.value,
                        entrada_id=compra.value,
                        produto_vexetal=produto_vexetal.value
                        if tipo.value == "postcolleita" else None,
                        instalacion_id=instalacion.value if tipo.value == "local" else None,
                        eficacia=eficacia.value, notas=notas.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value)
                    existente = (session.get(TratamentoInstalacion, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        novo = crear_tratamento_instalacion(session, actor_actual, horta_id, datos)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], novo)
                    else:
                        actualizar_tratamento_instalacion(session, actor_actual, existente,
                                                          datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("tratamento_instalacion", data.value)

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    def abrir(t: TratamentoInstalacion | None, tarefa: Tarefa | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = t.id if t else None
        titulo.text = _("Editar tratamento") if t else _("Apuntar tratamento")
        tipo.value = t.tipo if t else "postcolleita"
        data.value = (t.data if t else date.today()).isoformat()
        persoa.value = (t.persoa_id if t.persoa_id in persoas else None) if t else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{t.horas:g}" if t and t.horas else ""
        maquina.value = t.maquina_id if t and t.maquina_id in maquinas else None
        obxecto.value = t.obxecto if t else ""
        catastro.value = (t.referencia_catastral or "") if t else ""
        cantidade_tratada.value = f"{t.cantidade_tratada:g}" if t and t.cantidade_tratada \
            else ""
        tipo_problema.value = (t.problema_tipo or "praga") if t else "praga"
        problema.value = t.problema_codigo if t else None
        xustificacion.value = t.xustificacion if t else None
        tipo_produto.value = t.tipo_produto if t else None
        produto.value = t.produto_id if t and t.produto_id in por_id else None
        compra.set_options(compras.get(produto.value, {}),
                           value=t.entrada_id if t else None)
        nome_comercial.value = (t.nome_comercial or "") if t else ""
        num_rexistro.value = (t.num_rexistro or "") if t else ""
        materia_activa.value = (t.materia_activa or "") if t else ""
        cantidade.value = f"{t.cantidade_utilizada:g}" if t and t.cantidade_utilizada else ""
        unidade.value = t.unidade if t else None
        produto_vexetal.value = t.produto_vexetal if t else None
        instalacion.value = t.instalacion_id if t and t.instalacion_id in instalacions else None
        eficacia.value = t.eficacia if t else None
        notas.value = (t.notas or "") if t else ""
        cambiar_tipo()
        dialogo.open()

    return abrir
