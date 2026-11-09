"""Formularios da ficha do produto que sae, da clasificación e da mestura de lotes
. Clasificación e mestura son traballos: ábrense tamén
desde o Diario e as Tarefas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from io import BytesIO

import segno
from nicegui import ui

from horta.db import get_session
from horta.idiomas import _
from horta.models.lote import Clasificacion, Lote, Mestura, ProdutoVenda
from horta.models.tarefa import Tarefa
from horta.services.clasificacions import (
    DatosClasificacion,
    DatosMestura,
    OrixeMestura,
    actualizar_clasificacion,
    crear_clasificacion,
    crear_mestura,
    dar_de_baixa_clasificacion,
    dar_de_baixa_mestura,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.lotes import (
    AGRUPACIONS,
    CATEGORIAS_VENDA_DIRECTA,
    actualizar_ficha,
    actualizar_lote,
    clases_da_ficha,
    ficha_do_lote,
    listar_lotes,
    queda_por_clase,
)
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual

_CATEGORIAS = {clave: nome for clave, (nome, *_x) in CATEGORIAS_VENDA_DIRECTA.items()}


def texto_queda(queda: dict[str | None, float], unidade: str) -> str:
    partes = [f"{c}: {v:g}" for c, v in queda.items() if c is not None and v > 1e-9]
    if queda.get(None, 0) > 1e-9:
        partes.append(
            _("sen clasificar: {cantidade:g}").format(cantidade=queda[None])
            if partes
            else f"{queda[None]:g}"
        )
    return f"{', '.join(partes) or '0'} {unidade}"


def dialogo_ficha() -> Callable[[ProdutoVenda, Lote | None], None]:
    """A ficha do produto que vendes e, se se abre desde un lote, se ese lote é de
    invernadoiro (máximos da venda directa)."""
    ids: dict[str, int | None] = {"ficha": None, "lote": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        ui.label(_("Produto que vendes")).classes("text-h6")
        nome = ui.input(_("Nome")).classes("w-full")
        opcions_categoria = {c: _(n) for c, n in _CATEGORIAS.items()}
        categoria = ui.select(
            opcions_categoria,
            label=_("Tipo para a venda directa (Decreto 125/2014)"),
            clearable=True,
        ).classes("w-full")
        opcions_agrupacion = {c: _(t) for c, t in AGRUPACIONS.items()}
        agrupacion = ui.select(
            opcions_agrupacion,
            label=_("Como fas os lotes"),
        ).classes("w-full")
        clases = ui.input(
            _("Clases, separadas por comas (p.ex. grande, mediana, miúda)")
        ).classes("w-full")
        protexido = ui.checkbox(_("Este lote é de invernadoiro ou túnel"))

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                ficha = session.get(ProdutoVenda, ids["ficha"] or 0)
                lote = session.get(Lote, ids["lote"] or 0)
                if actor is None or ficha is None:
                    return

                def accion() -> None:
                    actualizar_ficha(session, actor, ficha, nome.value or "", categoria.value,
                                     (clases.value or "").split(","), agrupacion.value)
                    if lote is not None:
                        actualizar_lote(session, actor, lote, protexido.value)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button(_("Gardar"), icon="check", on_click=gardar)
            ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")

    def abrir(ficha: ProdutoVenda, lote: Lote | None = None) -> None:
        ids["ficha"], ids["lote"] = ficha.id, lote.id if lote else None
        nome.value = ficha.nome
        categoria.value = ficha.categoria_venda_directa
        agrupacion.value = ficha.agrupacion
        clases.value = ", ".join(clases_da_ficha(ficha))
        protexido.set_visibility(lote is not None)
        protexido.value = bool(lote and lote.protexido)
        dialogo.open()

    return abrir


def _quen_e_maquinas(horta_id: int) -> tuple[dict[int, str], dict[int, str]] | None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return None
        return ({p.id: p.nome for p in listar_quen(session, actor, horta_id)},
                {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)})


def dialogo_clasificacion(horta_id: int) -> Callable[..., None]:
    """abrir(clasificacion, tarefa=None, lote_id=None)."""
    listas = _quen_e_maquinas(horta_id)
    if listas is None:
        return lambda *_x, **_kw: None
    persoas, maquinas = listas
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(34rem, 94vw)"):
        titulo = ui.label(_("Clasificación")).classes("text-h6")
        ui.label(
            _("Repartir un lote por clases. O lote segue sendo o mesmo; o refugo conta como perda.")
        ).classes("texto-suave text-caption")
        lote = ui.select({}, label=_("Lote"), with_input=True).classes("w-full")
        queda = ui.label("").classes("text-caption")
        data = campo_data(_("Data"), date.today().isoformat())
        filas = ui.column().classes("w-full gap-0")
        refugo = ui.input(_("Refugo (podre, cortado…)")).classes("w-full")
        persoa = ui.select(persoas, label=_("Quen o fixo")).classes("w-full")
        with ui.expansion(_("Máis datos")).classes("w-full"):
            horas = ui.input(_("Horas de traballo")).classes("w-full")
            maquina = ui.select(maquinas, label=_("Máquina"), clearable=True).classes("w-full")
            notas = ui.textarea(_("Notas")).classes("w-full")
        campos: list[tuple[ui.input, ui.input]] = []

        def poñer_filas(clases: list[str], valores: dict[str, float]) -> None:
            filas.clear()
            campos.clear()
            nomes = clases or list(valores) or [""]
            with filas:
                for clase in [*nomes, *([""] if not clases else [])]:
                    with ui.row().classes("w-full no-wrap"):
                        nome = ui.input(_("Clase"), value=clase).classes("col")
                        nome.set_enabled(not clases)
                        canto = ui.input(_("Canto"), value=f"{valores[clase]:g}"
                                         if clase in valores else "").classes("col")
                        campos.append((nome, canto))

        def cambiar_lote() -> None:
            with get_session() as session:
                lt = session.get(Lote, lote.value or 0)
                if lt is None:
                    return
                ficha = ficha_do_lote(session, lt)
                q = queda_por_clase(session, lt, excepto_clasificacion=editando["id"])
                queda.text = _("Queda: {queda}").format(queda=texto_queda(q, lt.unidade))
                if not editando["id"]:
                    poñer_filas(clases_da_ficha(ficha), {})

        lote.on_value_change(cambiar_lote)

        def gardar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    dia = parsear_data(data.value)
                    if lote.value is None or dia is None:
                        raise OperacionNonPermitidaError(_("Escolle o lote e a data"))
                    clases = {n.value.strip(): parsear_decimal(c.value) or 0
                              for n, c in campos if (n.value or "").strip()}
                    datos = DatosClasificacion(
                        lote_id=lote.value, data=dia, clases=clases,
                        refugo=parsear_decimal(refugo.value) or 0, persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                        notas=notas.value or None)
                    existente = (session.get(Clasificacion, editando["id"])
                                 if editando["id"] else None)
                    if existente is None:
                        nova = crear_clasificacion(session, actor, datos)
                        rematar_tarefa(session, actor, editando["tarefa"], nova)
                    else:
                        actualizar_clasificacion(session, actor, existente, datos)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("clasificacion", data.value)

        def baixa() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                cl = session.get(Clasificacion, editando["id"] or 0)
                if actor is None or cl is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_clasificacion(
                    session, actor, cl))
            if ok:
                ui.navigate.reload()

        with ui.row().classes("w-full justify-between"):
            with ui.row():
                ui.button(_("Gardar"), icon="check", on_click=gardar)
                ui.button(_("Cancelar"), on_click=dialogo.close).props("flat")
            boton_baixa = ui.button(
                _("Dar de baixa"),
                icon="archive",
                on_click=lambda: (
                    confirmar_eliminacion(_("Dar de baixa esta clasificación?"), baixa)
                ),
            ).props("flat color=negative")

    def abrir(cl: Clasificacion | None, tarefa: Tarefa | None = None,
              lote_id: int | None = None) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            lotes = listar_lotes(session, actor, horta_id)
            clases_ficha = []
            if cl is not None:
                lt = session.get(Lote, cl.lote_id)
                clases_ficha = clases_da_ficha(ficha_do_lote(session, lt)) if lt else []
        editando["id"] = cl.id if cl else None
        editando["tarefa"] = tarefa.id if tarefa else None
        titulo.text = _("Editar clasificación") if cl else _("Clasificación")
        lote.set_options({lt.id: f"{lt.codigo} · {lt.produto}" for lt in lotes})
        lote.set_enabled(cl is None)
        data.value = (cl.data if cl else (tarefa.data if tarefa and tarefa.data
                                           else date.today())).isoformat()
        refugo.value = f"{cl.refugo:g}" if cl and cl.refugo else ""
        persoa.value = (cl.persoa_id if cl and cl.persoa_id in persoas else
                        None if cl else proposta_quen(horta_id, tarefa))
        horas.value = f"{cl.horas:g}" if cl and cl.horas else ""
        maquina.value = cl.maquina_id if cl and cl.maquina_id in maquinas else None
        notas.value = (cl.notas or "") if cl else ""
        lote.value = cl.lote_id if cl else lote_id
        if cl is not None:
            poñer_filas(clases_ficha, {c.clase: c.cantidade for c in cl.clases})
            cambiar_lote()
        elif lote_id is None:
            poñer_filas([], {})
        boton_baixa.set_visibility(cl is not None)
        dialogo.open()

    return abrir


def dialogo_mestura(horta_id: int) -> Callable[..., None]:
    """abrir(mestura, tarefa=None). Unha mestura gardada só se ve ou se dá de baixa."""
    listas = _quen_e_maquinas(horta_id)
    if listas is None:
        return lambda *_x, **_kw: None
    persoas, maquinas = listas
    estado: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label(_("Mestura de lotes")).classes("text-h6")
        ui.label(
            _("Xuntar lotes do mesmo produto nun lote novo, que garda de onde vén.")
        ).classes("texto-suave text-caption")
        vista = ui.column().classes("w-full gap-1")
        with ui.column().classes("w-full gap-0") as formulario:
            data = campo_data(_("Data"), date.today().isoformat())
            filas = ui.column().classes("w-full gap-0")
            ui.button(
                _("Outro lote"), icon="add", on_click=lambda: engadir_fila()
            ).props("flat dense")
            codigo = ui.input(
                _("Código do lote novo (baleiro: o que toque)")
            ).classes("w-full")
            persoa = ui.select(persoas, label=_("Quen o fixo")).classes("w-full")
            with ui.expansion(_("Máis datos")).classes("w-full"):
                horas = ui.input(_("Horas de traballo")).classes("w-full")
                maquina = ui.select(maquinas, label=_("Máquina"), clearable=True).classes("w-full")
                notas = ui.textarea(_("Notas")).classes("w-full")
        opcions: dict[str, str] = {}
        linas: list[tuple[ui.select, ui.input]] = []

        def engadir_fila() -> None:
            with filas, ui.row().classes("w-full no-wrap"):
                orixe = ui.select(opcions, label=_("Lote (e clase)"), with_input=True).classes(
                    "col")
                canto = ui.input(_("Canto")).classes("w-32")
                linas.append((orixe, canto))

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
                    orixes = []
                    for orixe, canto in linas:
                        if not orixe.value:
                            continue
                        lote_id, _sep, clase = str(orixe.value).partition("|")
                        orixes.append(OrixeMestura(lote_id=int(lote_id), clase=clase or None,
                                                    cantidade=parsear_decimal(canto.value) or 0))
                    nova = crear_mestura(session, actor, horta_id, DatosMestura(
                        data=dia, orixes=orixes, codigo=codigo.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None))
                    rematar_tarefa(session, actor, estado["tarefa"], nova)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("mestura", data.value)

        def baixa() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                mestura = session.get(Mestura, estado["id"] or 0)
                if actor is None or mestura is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_mestura(
                    session, actor, mestura))
            if ok:
                ui.navigate.reload()

        with ui.row().classes("w-full justify-between"):
            with ui.row():
                boton_gardar = ui.button(_("Gardar"), icon="check", on_click=gardar)
                ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
            boton_baixa = ui.button(
                _("Dar de baixa"),
                icon="archive",
                on_click=lambda: (
                    confirmar_eliminacion(_("Dar de baixa esta mestura?"), baixa)
                ),
            ).props("flat color=negative")

    def abrir(mestura: Mestura | None, tarefa: Tarefa | None = None) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            opcions.clear()
            for lt in listar_lotes(session, actor, horta_id):
                for clase, canto in queda_por_clase(session, lt).items():
                    if canto > 1e-9:
                        clase_str = f" · {clase}" if clase else ""
                        quedan_str = _("(quedan {canto:g} {unidade})").format(
                            canto=canto, unidade=lt.unidade
                        )
                        opcions[f"{lt.id}|{clase or ''}"] = (
                            f"{lt.codigo} · {lt.produto}{clase_str} {quedan_str}"
                        )
            textos: list[str] = []
            if mestura is not None:
                destino = session.get(Lote, mestura.lote_id)
                textos.append(
                    _("Lote novo: {codigo} · {data}").format(
                        codigo=destino.codigo if destino else "?",
                        data=f"{mestura.data:%d/%m/%Y}",
                    )
                )
                for o in mestura.orixes:
                    orixe = session.get(Lote, o.lote_id)
                    cod = orixe.codigo if orixe else "?"
                    if o.clase:
                        textos.append(
                            _("De {codigo}: {cantidade:g} ({clase})").format(
                                codigo=cod, cantidade=o.cantidade, clase=o.clase
                            )
                        )
                    else:
                        textos.append(
                            _("De {codigo}: {cantidade:g}").format(
                                codigo=cod, cantidade=o.cantidade
                            )
                        )
        estado["id"] = mestura.id if mestura else None
        estado["tarefa"] = tarefa.id if tarefa else None
        titulo.text = _("Mestura de lotes")
        vista.clear()
        with vista:
            for texto in textos:
                ui.label(texto)
        formulario.set_visibility(mestura is None)
        boton_gardar.set_visibility(mestura is None)
        boton_baixa.set_visibility(mestura is not None)
        if mestura is None:
            filas.clear()
            linas.clear()
            engadir_fila()
            engadir_fila()
            codigo.value = ""
            persoa.value = proposta_quen(horta_id, tarefa)
        dialogo.open()

    return abrir


def abrir_trazabilidade(lote_id: int) -> None:
    """Ficha de trazabilidade e simulacro de retirada dun lote: de onde veu, que se lle fixo,
    que pasou dentro e a onde foi. Pódese imprimir."""
    from horta.services.trazabilidade import trazabilidade

    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        traz = trazabilidade(session, actor, lote_id)
    with ui.dialog() as dialogo, ui.card().style("width: min(44rem, 96vw)"):
        ui.label(
            _("Trazabilidade do lote {codigo}").format(codigo=traz.lote.codigo)
        ).classes("text-h6")
        ui.label(
            _("{produto} · desde o {data}").format(
                produto=traz.lote.produto,
                data=f"{traz.lote.data:%d/%m/%Y}",
            )
        ).classes("texto-suave")
        seccions_traz = (
            (_("De onde veu"), traz.orixe),
            (_("Que se lle fixo"), traz.fixose),
            (_("Dentro do lote"), traz.dentro),
            (_("A onde foi"), traz.saidas),
        )
        for titulo, lineas in seccions_traz:
            ui.label(titulo).classes("text-subtitle1 text-weight-bold q-mt-sm")
            if not lineas:
                ui.label(_("Nada apuntado.")).classes("texto-suave")
            for linea in lineas:
                data = f"{linea.data:%d/%m/%Y} · " if linea.data else ""
                ui.label(f"{data}{linea.texto}")
        with ui.row():
            ui.button(
                _("Imprimir"),
                icon="print",
                on_click=lambda: ui.run_javascript("window.print()"),
            ).props("outline")
            ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
    dialogo.open()


def dialogo_transformacion(horta_id: int) -> Callable[..., None]:
    """abrir(transformacion, tarefa=None). Unha gardada só se ve ou se dá de baixa."""
    from horta.models.lote import Transformacion
    from horta.models.produto import Produto
    from horta.services.clasificacions import (
        DatosTransformacion,
        InsumoTransformacion,
        crear_transformacion,
        dar_de_baixa_transformacion,
    )
    from horta.services.instalacions import listar_instalacions
    from horta.services.lotes import listar_fichas
    from horta.services.produtos import listar_produtos

    listas = _quen_e_maquinas(horta_id)
    if listas is None:
        return lambda *_x, **_kw: None
    persoas, maquinas = listas
    estado: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog().props("persistent") as dialogo, ui.card().style("width: min(40rem, 96vw)"):
        ui.label(_("Transformación")).classes("text-h6")
        ui.label(
            _("Elaborar un produto novo con lotes propios e ingredientes mercados. "
              "Sae un lote novo que garda de onde vén.")
        ).classes("texto-suave text-caption")
        vista = ui.column().classes("w-full gap-1")
        with ui.column().classes("w-full gap-0") as formulario:
            data = campo_data(_("Data"), date.today().isoformat())
            with ui.row().classes("w-full no-wrap"):
                produto = ui.select([], label=_("Que sae (p.ex. Conserva de pemento)"),
                                    with_input=True, new_value_mode="add-unique").classes("col")
                canto = ui.input(_("Canto")).classes("w-24")
                unidade = ui.select(["unidades", "kg", "litros"], value="unidades",
                                    label=_("Unidade")).classes("w-32")
            ui.label(_("Lotes que entran")).classes("text-subtitle2 q-mt-sm")
            filas_lotes = ui.column().classes("w-full gap-0")
            ui.button(_("Outro lote"), icon="add", on_click=lambda: fila_lote()).props(
                "flat dense")
            ui.label(_("Ingredientes e envases mercados")).classes("text-subtitle2")
            filas_insumos = ui.column().classes("w-full gap-0")
            ui.button(
                _("Outro ingrediente"), icon="add", on_click=lambda: fila_insumo()
            ).props("flat dense")
            codigo = ui.input(
                _("Código do lote novo (baleiro: o que toque)")
            ).classes("w-full")
            instalacion = ui.select({}, label=_("Onde (instalación)"), clearable=True).classes(
                "w-full")
            persoa = ui.select(persoas, label=_("Quen o fixo")).classes("w-full")
            with ui.expansion(_("Máis datos")).classes("w-full"):
                horas = ui.input(_("Horas de traballo")).classes("w-full")
                maquina = ui.select(maquinas, label=_("Máquina"), clearable=True).classes("w-full")
                notas = ui.textarea(_("Notas")).classes("w-full")
        opcions_lotes: dict[str, str] = {}
        opcions_produtos: dict[int, str] = {}
        lotes_linas: list[tuple[ui.select, ui.input]] = []
        insumos_linas: list[tuple[ui.select, ui.input]] = []

        def fila_lote() -> None:
            with filas_lotes, ui.row().classes("w-full no-wrap"):
                lotes_linas.append((ui.select(opcions_lotes, label=_("Lote (e clase)"),
                                              with_input=True).classes("col"),
                                    ui.input(_("Canto")).classes("w-28")))

        def fila_insumo() -> None:
            with filas_insumos, ui.row().classes("w-full no-wrap"):
                insumos_linas.append((ui.select(opcions_produtos, label=_("Produto"),
                                                with_input=True).classes("col"),
                                      ui.input(_("Canto")).classes("w-28")))

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
                    entradas = []
                    for orixe, cantidade in lotes_linas:
                        if orixe.value:
                            lote_id, _sep, clase = str(orixe.value).partition("|")
                            entradas.append(OrixeMestura(
                                lote_id=int(lote_id), clase=clase or None,
                                cantidade=parsear_decimal(cantidade.value) or 0))
                    insumos = [InsumoTransformacion(produto_id=p.value,
                                                     cantidade=parsear_decimal(c.value) or 0)
                                for p, c in insumos_linas if p.value]
                    nova = crear_transformacion(session, actor, horta_id, DatosTransformacion(
                        data=dia, produto=produto.value or "", unidade=unidade.value,
                        cantidade=parsear_decimal(canto.value) or 0, entradas=entradas,
                        insumos=insumos, codigo=codigo.value or None,
                        instalacion_id=instalacion.value, persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value), maquina_id=maquina.value,
                        notas=notas.value or None))
                    rematar_tarefa(session, actor, estado["tarefa"], nova)

                ok = executar_accion(session, accion)
            if ok:
                recargar_apuntado("transformacion", data.value)

        def baixa() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                tr = session.get(Transformacion, estado["id"] or 0)
                if actor is None or tr is None:
                    return
                ok = executar_accion(session, lambda: dar_de_baixa_transformacion(
                    session, actor, tr))
            if ok:
                ui.navigate.reload()

        with ui.row().classes("w-full justify-between"):
            with ui.row():
                boton_gardar = ui.button(_("Gardar"), icon="check", on_click=gardar)
                ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
            boton_baixa = ui.button(
                _("Dar de baixa"),
                icon="archive",
                on_click=lambda: (
                    confirmar_eliminacion(_("Dar de baixa esta transformación?"), baixa)
                ),
            ).props("flat color=negative")

    def abrir(tr: Transformacion | None, tarefa: Tarefa | None = None) -> None:
        with get_session() as session:
            actor = usuario_actual(session)
            if actor is None:
                pechar_sesion()
                return
            opcions_lotes.clear()
            for lt in listar_lotes(session, actor, horta_id):
                for clase, cantidade in queda_por_clase(session, lt).items():
                    if cantidade > 1e-9:
                        clase_str = f" · {clase}" if clase else ""
                        quedan_str = _("(quedan {canto:g} {unidade})").format(
                            canto=cantidade, unidade=lt.unidade
                        )
                        opcions_lotes[f"{lt.id}|{clase or ''}"] = (
                            f"{lt.codigo} · {lt.produto}{clase_str} {quedan_str}"
                        )
            opcions_produtos.clear()
            opcions_produtos.update({p.id: f"{p.nome} ({p.unidade})"
                                     for p in listar_produtos(session, actor, horta_id)})
            produto.set_options(sorted({f.nome for f in listar_fichas(session, actor,
                                                                       horta_id)}))
            instalacion.set_options({i.id: i.nome for i in listar_instalacions(
                session, actor, horta_id, so_activas=True)})
            textos: list[str] = []
            if tr is not None:
                destino = session.get(Lote, tr.lote_id)
                textos.append(
                    _("{data} · saíron {cantidade:g} {unidade} no lote {codigo}").format(
                        data=f"{tr.data:%d/%m/%Y}",
                        cantidade=tr.cantidade,
                        unidade=destino.unidade if destino else "",
                        codigo=destino.codigo if destino else "?",
                    )
                )
                for e in tr.entradas:
                    orixe = session.get(Lote, e.lote_id)
                    cod = orixe.codigo if orixe else "?"
                    if e.clase:
                        textos.append(
                            _("De {codigo}: {cantidade:g} ({clase})").format(
                                codigo=cod, cantidade=e.cantidade, clase=e.clase
                            )
                        )
                    else:
                        textos.append(
                            _("De {codigo}: {cantidade:g}").format(
                                codigo=cod, cantidade=e.cantidade
                            )
                        )
                for i in tr.insumos:
                    p = session.get(Produto, i.produto_id)
                    textos.append(
                        _("Ingrediente: {nome} {cantidade:g}").format(
                            nome=p.nome if p else "?",
                            cantidade=i.cantidade,
                        )
                    )
        estado["id"] = tr.id if tr else None
        estado["tarefa"] = tarefa.id if tarefa else None
        vista.clear()
        with vista:
            for texto in textos:
                ui.label(texto)
        formulario.set_visibility(tr is None)
        boton_gardar.set_visibility(tr is None)
        boton_baixa.set_visibility(tr is not None)
        if tr is None:
            filas_lotes.clear()
            lotes_linas.clear()
            filas_insumos.clear()
            insumos_linas.clear()
            fila_lote()
            fila_insumo()
            codigo.value = ""
            canto.value = ""
            persoa.value = proposta_quen(horta_id, tarefa)
        dialogo.open()

    return abrir


def abrir_paxina_publica(lote_id: int) -> None:
    """Publicar o lote (enderezo secreto para quen merca) ou retirar a publicación."""
    from horta.services.trazabilidade import publicar_lote, retirar_publicacion

    with get_session() as session:
        actor = usuario_actual(session)
        lote = session.get(Lote, lote_id)
        if actor is None or lote is None:
            return
        try:
            token = publicar_lote(session, actor, lote)
        except OperacionNonPermitidaError as erro:
            ui.notify(str(erro), type="negative")
            return
    with ui.dialog() as dialogo, ui.card().style("width: min(34rem, 94vw)"):
        ui.label(
            _("Páxina pública do lote {codigo}").format(codigo=lote.codigo)
        ).classes("text-h6")
        ui.label(
            _("Quen teña este enderezo ve de onde vén o produto e que se lle fixo "
              "(nunca a quen se vendeu). Pódese poñer na etiqueta.")
        ).classes("text-caption")
        enderezo = ui.label("").classes("text-weight-bold")
        qr = ui.image().style("width: 12rem")
        ligazon: dict[str, str] = {}

        async def amosar() -> None:
            orixe = await ui.run_javascript("window.location.origin")
            ligazon["url"] = f"{orixe}/lote/{token}"
            enderezo.set_text(ligazon["url"])
            qr.set_source(segno.make(ligazon["url"], error="m").svg_data_uri(scale=6))

        ui.timer(0.1, amosar, once=True)

        def descargar_qr() -> None:
            if "url" not in ligazon:
                return
            saida = BytesIO()
            segno.make(ligazon["url"], error="m").save(saida, kind="png", scale=10)
            ui.download.content(saida.getvalue(), f"qr-lote-{lote.codigo}.png")

        def retirar() -> None:
            with get_session() as session:
                actor = usuario_actual(session)
                lt = session.get(Lote, lote_id)
                if actor is None or lt is None:
                    return
                ok = executar_accion(session, lambda: retirar_publicacion(session, actor, lt))
            if ok:
                dialogo.close()
                ui.notify(_("Retirada: o enderezo xa non funciona"))

        with ui.row():
            ui.button(_("Descargar o QR"), icon="qr_code", on_click=descargar_qr)
            ui.button(_("Abrir"), icon="open_in_new",
                      on_click=lambda: ui.navigate.to(f"/lote/{token}", new_tab=True))
            ui.button(_("Retirar"), icon="link_off", on_click=retirar).props(
                "flat color=negative"
            )
            ui.button(_("Pechar"), on_click=dialogo.close).props("flat")
    dialogo.open()
