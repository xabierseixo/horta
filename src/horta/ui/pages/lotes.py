"""Sección Lotes: o produto que sae da explotación. Cada lote co que entrou (colleitas e
produción dos animais), o que saíu e o que queda; e as súas saídas: venda, casa,
transformación, perda e animais."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.lote import Lote, LoteSaida
from horta.models.tarefa import Tarefa
from horta.services.errors import OperacionNonPermitidaError
from horta.services.lotes import (
    CANLES,
    CATEGORIAS_VENDA_DIRECTA,
    TIPOS_SAIDA,
    DatosSaida,
    actualizar_saida,
    avisos_saida,
    converter,
    crear_saida,
    dar_de_baixa_saida,
    listar_fichas,
    listar_lotes,
    listar_saidas,
    queda_por_clase,
    resumo_lotes,
)
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas, listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campo_pago import CampoPago
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.fotos import abrir_fotos
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.pages.clasificacions import (
    dialogo_clasificacion,
    dialogo_ficha,
    dialogo_mestura,
    texto_queda,
)
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_UNIDADES = ("kg", "t", "unidades", "ducias", "litros", "mazos")
_CATEGORIAS = {clave: nome for clave, (nome, *_) in CATEGORIAS_VENDA_DIRECTA.items()}


def _canto(cantidade: float, unidade: str) -> str:
    return f"{cantidade:g} {unidade}"


def seccion_lotes(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        lotes = listar_lotes(session, actor, horta_id)
        resumo = resumo_lotes(session, actor, horta_id)
        saidas = listar_saidas(session, actor, horta_id)
        fichas = {f.id: f for f in listar_fichas(session, actor, horta_id)}
        por_clase = {lote.id: queda_por_clase(session, lote) for lote in lotes}
        nomes = {p.id: p.nome for p in listar_persoas(session, actor, horta_id,
                                                       so_activas=False)}
    por_id = {lote.id: lote for lote in lotes}

    filas = [{
        "id": lote.id,
        "codigo": lote.codigo,
        "produto": lote.produto,
        "entrou": _canto(resumo[lote.id][0], lote.unidade),
        "saiu": _canto(resumo[lote.id][1], lote.unidade),
        "queda": texto_queda(por_clase[lote.id], lote.unidade),
        "categoria": _CATEGORIAS.get(
            fichas[lote.produto_venda_id].categoria_venda_directa or "", ""),
    } for lote in lotes]
    taboa = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("codigo", "Lote"), ("produto", "Produto"), ("queda", "Queda"),
            ("entrou", "Entrou"), ("saiu", "Saíu"), ("categoria", "Venda directa"))],
        rows=filas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        'flat bordered no-data-label="Aínda non hai lotes: saen das colleitas e da '
        f'produción dos animais" {TEXTOS_TABOA}')

    abrir = dialogo_saida(horta_id) if pode_editar else None
    if pode_editar and abrir is not None:
        abrir_ficha = dialogo_ficha()
        abrir_clasificacion = dialogo_clasificacion(horta_id)
        abrir_mestura = dialogo_mestura(horta_id)

        def lote_escollido() -> int | None:
            if not taboa.selected:
                ui.notify("Escolle primeiro un lote na táboa", type="warning")
                return None
            return int(taboa.selected[0]["id"])

        def vender() -> None:
            lote_id = lote_escollido()
            if lote_id is not None:
                abrir(None, None, lote_id, "venda")

        def outra() -> None:
            lote_id = lote_escollido()
            if lote_id is not None:
                abrir(None, None, lote_id, "casa")

        def ficha() -> None:
            lote_id = lote_escollido()
            if lote_id is not None:
                lote = por_id[lote_id]
                abrir_ficha(fichas[lote.produto_venda_id], lote)

        def clasificar() -> None:
            lote_id = lote_escollido()
            if lote_id is not None:
                abrir_clasificacion(None, None, lote_id)

        def fotos() -> None:
            lote_id = lote_escollido()
            if lote_id is not None:
                abrir_fotos(horta_id, "lote", lote_id, por_id[lote_id].codigo, pode_editar)

        with ui.row():
            ui.button("Vender", icon="sell", on_click=vender)
            ui.button("Fotos", icon="photo_camera", on_click=fotos).props("outline")
            ui.button("Outra saída", icon="output", on_click=outra).props("outline")
            ui.button("Clasificar", icon="filter_list", on_click=clasificar).props("outline")
            ui.button("Mesturar lotes", icon="merge", on_click=lambda: abrir_mestura(None)
                      ).props("outline")
            ui.button("Ficha do produto", icon="tune", on_click=ficha).props("outline")

    ui.label("Saídas").classes("text-h6 q-mt-md")
    filas_saidas = [{
        "id": s.id,
        "data": (f"{s.data:%d/%m/%Y}" if s.data_fin == s.data
                 else f"{s.data:%d/%m} – {s.data_fin:%d/%m/%Y}"),
        "lote": por_id[s.lote_id].codigo if s.lote_id in por_id else "",
        "que": TIPOS_SAIDA[s.tipo].split(" (")[0],
        "canto": _canto(s.cantidade, s.unidade),
        "a_quen": " · ".join(x for x in (CANLES.get(s.canle or "", ""),
                                         nomes.get(s.comprador_id or 0, ""), s.lugar or "")
                             if x),
        "prezo": f"{s.importe:.2f} €" if s.importe is not None else "",
        "quen": nomes.get(s.persoa_id or 0, ""),
    } for s in saidas]
    taboa_saidas = ui.table(
        columns=[{"name": k, "label": etiqueta, "field": k} for k, etiqueta in (
            ("data", "Data"), ("que", "Que"), ("canto", "Canto"), ("lote", "Lote"),
            ("a_quen", "A quen"), ("prezo", "Prezo"), ("quen", "Quen"))],
        rows=filas_saidas, row_key="id", selection="single" if pode_editar else None,
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non saíu nada" {TEXTOS_TABOA}')
    if not pode_editar or abrir is None:
        return

    def editar() -> None:
        if not taboa_saidas.selected:
            ui.notify("Escolle primeiro unha saída na táboa", type="warning")
            return
        with get_session() as session:
            saida = session.get(LoteSaida, taboa_saidas.selected[0]["id"])
        if saida is not None:
            abrir(saida)

    def dar_de_baixa() -> None:
        if not taboa_saidas.selected:
            ui.notify("Escolle primeiro unha saída na táboa", type="warning")
            return
        saida_id = taboa_saidas.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                saida = session.get(LoteSaida, saida_id)
                if actor_actual is None or saida is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_saida(
                    session, actor_actual, saida))
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta saída? Non se borra: consérvase no histórico.", confirmar)

    with ui.row():
        ui.button("Editar", icon="edit", on_click=editar).props("outline")
        ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


def dialogo_saida(horta_id: int) -> Callable[..., None]:
    """Constrúe o diálogo de apuntar ou editar unha saída de produto e devolve a función que o
    abre: abrir(saida, tarefa=None, lote_id=None, tipo=None)."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_, **__: None
        lotes = listar_lotes(session, actor, horta_id)
        resumo = resumo_lotes(session, actor, horta_id)
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}
    unidades_lote = {lote.id: lote.unidade for lote in lotes}
    opcions_lote = {lote.id: f"{lote.codigo} · {lote.produto} (quedan "
                             f"{_canto(resumo[lote.id][2], lote.unidade)})" for lote in lotes}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Saída de produto").classes("text-h6")
        if not lotes:
            ui.label("Aínda non hai lotes: saen das colleitas e da produción dos animais."
                     ).classes("text-warning text-caption")
        lote = ui.select(opcions_lote, label="Lote", with_input=True).classes("w-full")
        tipo = ui.select(TIPOS_SAIDA, label="A onde vai", value="venda").classes("w-full")
        clase = ui.select({}, label="Clase (tamaño, calidade…)", clearable=True).classes(
            "w-full")
        with ui.row().classes("w-full no-wrap"):
            data = campo_data("Data", date.today().isoformat()).classes(
                remove="w-full", add="col")
            data_fin = campo_data("Ata (opcional)", "").classes(remove="w-full", add="col")
        with ui.row().classes("w-full no-wrap"):
            cantidade = ui.input("Canto").classes("col")
            unidade = ui.select(list(_UNIDADES), label="Unidade", value="kg").classes("col")
        with ui.column().classes("w-full gap-0") as bloque_venda:
            canle = ui.select(CANLES, label="A quen ou onde", value="explotacion").classes(
                "w-full")
            lugar = ui.input("Lugar (p.ex. mercado de Lalín)").classes("w-full")
            comprador = CampoPersoa(horta_id, "cliente", "Quen merca")
            with ui.row().classes("w-full no-wrap"):
                albaran = ui.input("Nº de albará ou factura").classes("col")
                importe = ui.input("Prezo total (€)").classes("col")
            cobro = CampoPago("Cobrada")
        aviso = ui.label("").classes("etiqueta-aviso")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")

        def datos() -> DatosSaida | None:
            inicio = parsear_data(data.value)
            if lote.value is None or inicio is None:
                return None
            canto = parsear_decimal(cantidade.value)
            return DatosSaida(
                lote_id=lote.value, data=inicio, data_fin=parsear_data(data_fin.value),
                tipo=tipo.value, cantidade=canto if canto is not None else 0,
                unidade=unidade.value, persoa_id=persoa.value, canle=canle.value,
                clase=clase.value or None,
                lugar=lugar.value or None, comprador_id=comprador.value,
                albaran_factura=albaran.value or None, importe=parsear_decimal(importe.value),
                data_pago=cobro.valor(parsear_data(data_fin.value) or inicio),
                horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                notas=notas.value or None)

        def avisar() -> None:
            bloque_venda.set_visibility(tipo.value == "venda")
            comprador.set_label("Que tenda, almacén ou cooperativa"
                                if canle.value in ("tenda", "almacen") else "Quen merca")
            textos: list[str] = []
            try:
                d = datos()
            except ValueError:
                d = None
            if d is not None:
                with get_session() as session:
                    actor_actual = usuario_actual(session)
                    if actor_actual is not None:
                        textos = avisos_saida(session, actor_actual, d, editando["id"])
            aviso.text = " ".join(textos)
            aviso.set_visibility(bool(textos))

        def cambiar_lote() -> None:
            # As clases do lote, se se clasificou
            with get_session() as session:
                escollido = session.get(Lote, lote.value or 0)
                quedan = queda_por_clase(session, escollido, editando["id"]) if escollido else {}
            clases = {c: f"{c} (quedan {v:g})" for c, v in quedan.items() if c is not None}
            clase.set_options(clases, value=clase.value if clase.value in clases else None)
            clase.set_visibility(bool(clases))
            # A unidade do lote, ou unha que se poida converter a ela
            if lote.value in unidades_lote:
                base = unidades_lote[lote.value]
                opcions = [u for u in _UNIDADES if converter(1, u, base) is not None]
                unidade.set_options(opcions, value=unidade.value if unidade.value in opcions
                                    and editando["id"] is not None else base)
            avisar()

        lote.on_value_change(cambiar_lote)
        for campo in (tipo, canle, data, cantidade, unidade):
            campo.on_value_change(avisar)

        def gardar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    d = datos()
                    if d is None:
                        raise OperacionNonPermitidaError("Escolle o lote e a data")
                    existente = (session.get(LoteSaida, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        nova = crear_saida(session, actor_actual, d)
                        rematar_tarefa(session, actor_actual, editando["tarefa"], nova)
                    else:
                        actualizar_saida(session, actor_actual, existente, d)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(saida: LoteSaida | None, tarefa: Tarefa | None = None,
              lote_id: int | None = None, tipo_saida: str | None = None) -> None:
        editando["tarefa"] = tarefa.id if tarefa else None
        editando["id"] = saida.id if saida else None
        titulo.text = "Editar saída de produto" if saida else "Saída de produto"
        lote.value = saida.lote_id if saida else lote_id
        tipo.value = saida.tipo if saida else (tipo_saida or "venda")
        data.value = (saida.data if saida else date.today()).isoformat()
        data_fin.value = (saida.data_fin.isoformat()
                          if saida and saida.data_fin != saida.data else "")
        cantidade.value = f"{saida.cantidade:g}" if saida else ""
        clase.value = None
        cambiar_lote()
        clase.value = saida.clase if saida and saida.clase in clase.options else None
        if saida:
            unidade.value = saida.unidade
        canle.value = (saida.canle if saida and saida.canle else "explotacion")
        lugar.value = (saida.lugar or "") if saida else ""
        comprador.value = saida.comprador_id if saida else None
        albaran.value = (saida.albaran_factura or "") if saida else ""
        importe.value = f"{saida.importe:g}" if saida and saida.importe is not None else ""
        cobro.poñer(saida.data_pago if saida else None, saida is None)
        persoa.value = (saida.persoa_id if saida.persoa_id in persoas else None) if saida else (
            proposta_quen(horta_id, tarefa))
        horas.value = f"{saida.horas:g}" if saida and saida.horas else ""
        maquina.value = saida.maquina_id if saida and saida.maquina_id in maquinas else None
        notas.value = (saida.notas or "") if saida else ""
        avisar()
        dialogo.open()

    return abrir
