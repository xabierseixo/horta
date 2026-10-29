"""Formularios da ficha do produto que sae, da clasificación e da mestura de lotes
. Clasificación e mestura son traballos: ábrense tamén
desde o Diario e as Tarefas."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
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
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual

_CATEGORIAS = {clave: nome for clave, (nome, *_) in CATEGORIAS_VENDA_DIRECTA.items()}


def texto_queda(queda: dict[str | None, float], unidade: str) -> str:
    partes = [f"{c}: {v:g}" for c, v in queda.items() if c is not None and v > 1e-9]
    if queda.get(None, 0) > 1e-9:
        partes.append(f"sen clasificar: {queda[None]:g}" if partes else f"{queda[None]:g}")
    return f"{', '.join(partes) or '0'} {unidade}"


def dialogo_ficha() -> Callable[[ProdutoVenda, Lote | None], None]:
    """A ficha do produto que vendes e, se se abre desde un lote, se ese lote é de
    invernadoiro (máximos da venda directa)."""
    ids: dict[str, int | None] = {"ficha": None, "lote": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        ui.label("Produto que vendes").classes("text-h6")
        nome = ui.input("Nome").classes("w-full")
        categoria = ui.select(_CATEGORIAS, label="Tipo para a venda directa (Decreto 125/2014)",
                              clearable=True).classes("w-full")
        agrupacion = ui.select(AGRUPACIONS, label="Como fas os lotes").classes("w-full")
        clases = ui.input("Clases, separadas por comas (p.ex. grande, mediana, miúda)"
                          ).classes("w-full")
        protexido = ui.checkbox("Este lote é de invernadoiro ou túnel")

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
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

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
        return lambda *_, **__: None
    persoas, maquinas = listas
    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(34rem, 94vw)"):
        titulo = ui.label("Clasificación").classes("text-h6")
        ui.label("Repartir un lote por clases. O lote segue sendo o mesmo; o refugo conta como "
                 "perda.").classes("texto-suave text-caption")
        lote = ui.select({}, label="Lote", with_input=True).classes("w-full")
        queda = ui.label("").classes("text-caption")
        data = campo_data("Data", date.today().isoformat())
        filas = ui.column().classes("w-full gap-0")
        refugo = ui.input("Refugo (podre, cortado…)").classes("w-full")
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.expansion("Máis datos").classes("w-full"):
            horas = ui.input("Horas de traballo").classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            notas = ui.textarea("Notas").classes("w-full")
        campos: list[tuple[ui.input, ui.input]] = []

        def poñer_filas(clases: list[str], valores: dict[str, float]) -> None:
            filas.clear()
            campos.clear()
            nomes = clases or list(valores) or [""]
            with filas:
                for clase in [*nomes, *([""] if not clases else [])]:
                    with ui.row().classes("w-full no-wrap"):
                        nome = ui.input("Clase", value=clase).classes("col")
                        nome.set_enabled(not clases)
                        canto = ui.input("Canto", value=f"{valores[clase]:g}"
                                         if clase in valores else "").classes("col")
                        campos.append((nome, canto))

        def cambiar_lote() -> None:
            with get_session() as session:
                lt = session.get(Lote, lote.value or 0)
                if lt is None:
                    return
                ficha = ficha_do_lote(session, lt)
                q = queda_por_clase(session, lt, excepto_clasificacion=editando["id"])
                queda.text = f"Queda: {texto_queda(q, lt.unidade)}"
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
                        raise OperacionNonPermitidaError("Escolle o lote e a data")
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
                ui.navigate.reload()

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
                ui.button("Gardar", icon="check", on_click=gardar)
                ui.button("Cancelar", on_click=dialogo.close).props("flat")
            boton_baixa = ui.button("Dar de baixa", icon="archive", on_click=lambda: (
                confirmar_eliminacion("Dar de baixa esta clasificación?", baixa))).props(
                "flat color=negative")

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
        titulo.text = "Editar clasificación" if cl else "Clasificación"
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
        return lambda *_, **__: None
    persoas, maquinas = listas
    estado: dict[str, int | None] = {"id": None, "tarefa": None}
    with ui.dialog() as dialogo, ui.card().style("width: min(36rem, 94vw)"):
        titulo = ui.label("Mestura de lotes").classes("text-h6")
        ui.label("Xuntar lotes do mesmo produto nun lote novo, que garda de onde vén."
                 ).classes("texto-suave text-caption")
        vista = ui.column().classes("w-full gap-1")
        with ui.column().classes("w-full gap-0") as formulario:
            data = campo_data("Data", date.today().isoformat())
            filas = ui.column().classes("w-full gap-0")
            ui.button("Outro lote", icon="add", on_click=lambda: engadir_fila()).props(
                "flat dense")
            codigo = ui.input("Código do lote novo (baleiro: o que toque)").classes("w-full")
            persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
            with ui.expansion("Máis datos").classes("w-full"):
                horas = ui.input("Horas de traballo").classes("w-full")
                maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
                notas = ui.textarea("Notas").classes("w-full")
        opcions: dict[str, str] = {}
        linas: list[tuple[ui.select, ui.input]] = []

        def engadir_fila() -> None:
            with filas, ui.row().classes("w-full no-wrap"):
                orixe = ui.select(opcions, label="Lote (e clase)", with_input=True).classes(
                    "col")
                canto = ui.input("Canto").classes("w-32")
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
                        raise OperacionNonPermitidaError("Indica a data")
                    orixes = []
                    for orixe, canto in linas:
                        if not orixe.value:
                            continue
                        lote_id, _, clase = str(orixe.value).partition("|")
                        orixes.append(OrixeMestura(lote_id=int(lote_id), clase=clase or None,
                                                   cantidade=parsear_decimal(canto.value) or 0))
                    nova = crear_mestura(session, actor, horta_id, DatosMestura(
                        data=dia, orixes=orixes, codigo=codigo.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
                        maquina_id=maquina.value, notas=notas.value or None))
                    rematar_tarefa(session, actor, estado["tarefa"], nova)

                ok = executar_accion(session, accion)
            if ok:
                ui.navigate.reload()

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
                boton_gardar = ui.button("Gardar", icon="check", on_click=gardar)
                ui.button("Pechar", on_click=dialogo.close).props("flat")
            boton_baixa = ui.button("Dar de baixa", icon="archive", on_click=lambda: (
                confirmar_eliminacion("Dar de baixa esta mestura?", baixa))).props(
                "flat color=negative")

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
                        opcions[f"{lt.id}|{clase or ''}"] = (
                            f"{lt.codigo} · {lt.produto}{f' · {clase}' if clase else ''} "
                            f"(quedan {canto:g} {lt.unidade})")
            textos: list[str] = []
            if mestura is not None:
                destino = session.get(Lote, mestura.lote_id)
                textos.append(f"Lote novo: {destino.codigo if destino else '?'} · "
                              f"{mestura.data:%d/%m/%Y}")
                for o in mestura.orixes:
                    orixe = session.get(Lote, o.lote_id)
                    textos.append(f"De {orixe.codigo if orixe else '?'}: {o.cantidade:g}"
                                  f"{f' ({o.clase})' if o.clase else ''}")
        estado["id"] = mestura.id if mestura else None
        estado["tarefa"] = tarefa.id if tarefa else None
        titulo.text = "Mestura de lotes"
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
