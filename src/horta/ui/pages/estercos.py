"""Sección de estercos e purín: cesións e recepcións (RD 1051/2022)."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.esterco import MovementoEsterco
from horta.models.persoa import Persoa
from horta.models.tarefa import Tarefa
from horta.services.animais import ESPECIES
from horta.services.catalogos import describir, valores_vixentes
from horta.services.errors import OperacionNonPermitidaError
from horta.services.estercos import (
    ORIXES_COMPOSICION,
    actualizar_movemento,
    crear_movemento,
    dar_de_baixa_movemento,
    documento_anexo_vii,
    faltas_documento,
    listar_movementos,
    resumo_ano,
)
from horta.services.fertilizantes import ESTERCOS
from horta.services.persoas import listar_persoas, listar_quen, nome_completo
from horta.services.textos_catalogo import texto_catalogo
from horta.ui.accions import executar_accion, recargar_apuntado
from horta.ui.campo_persoa import CampoPersoa
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.facer_tarefa import rematar_tarefa
from horta.ui.formato_descarga import descargar_informe, selector_formato
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

COLUMNAS_TABOA = [
    {"name": "data", "label": "Data", "field": "data", "align": "left"},
    {"name": "tipo", "label": "Tipo", "field": "tipo", "align": "left"},
    {"name": "outra_parte", "label": "Outra parte", "field": "outra_parte", "align": "left"},
    {"name": "material", "label": "Material", "field": "material", "align": "left"},
    {"name": "cantidade", "label": "Cantidade", "field": "cantidade", "align": "left"},
    {"name": "n_total", "label": "N (%)", "field": "n_total", "align": "left"},
    {
        "name": "orixe_composicion",
        "label": "Orixe da composición",
        "field": "orixe_composicion",
        "align": "left",
    },
    {
        "name": "faltas",
        "label": "Faltan datos",
        "field": "faltas",
        "align": "left",
        "classes": "text-warning",
    },
]


def texto_tipo_movemento(tipo: str) -> str:
    """Devolve a etiqueta en galego do tipo de movemento."""
    return "Cesión" if tipo == "cesion" else "Recepción"


def texto_faltas_documento(faltas: list[str]) -> str:
    """Xunta as faltas de datos nunha soa cadea de texto."""
    return ", ".join(faltas)


def texto_resumo_material(descricion: str, cantidade: float, unidade: str) -> str:
    """Texto descritivo dun total por material no resumo."""
    return f"{descricion}: {cantidade:g} {unidade}"


def texto_resumo_n(kg_n: float) -> str:
    """Texto descritivo do total de nitróxeno."""
    return f"{kg_n:g} kg"


def dialogo_esterco(
    horta_id: int,
) -> Callable[[MovementoEsterco | None, Tarefa | None], None]:
    """Constrúe o diálogo de apuntar ou editar un movemento de esterco."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return lambda *_: None
        materiais_cat = {
            v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
            for v in valores_vixentes(session, "material_fertilizante")
            if v.codigo in ESTERCOS
        }
        if not materiais_cat:
            materiais_cat = {c: f"Esterco ou purín ({c})" for c in sorted(ESTERCOS)}
        persoas_quen = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None, "tarefa": None}
    cargando = False

    with (
        ui.dialog().props("persistent") as dialogo,
        ui.card().style("width: min(42rem, 94vw)"),
    ):
        titulo = ui.label("Nova cesión ou recepción").classes("text-h6")
        ui.label(
            "O RD 1051/2022 pide entregar este documento a quen recibe o esterco."
        ).classes("text-caption texto-suave")

        with ui.row().classes("w-full no-wrap gap-2"):
            tipo = ui.select(
                {"cesion": "Cesión", "recepcion": "Recepción"},
                label="Tipo de movemento",
                value="cesion",
            ).classes("col")
            data = campo_data("Data", date.today().isoformat())

        outra_parte = CampoPersoa(horta_id, "explotacion", "Outra parte (persoa ou entidade)")
        outra_parte_rega = ui.input("Código REGA ou NIMA da outra parte").classes("w-full")

        def ao_cambiar_outra_parte() -> None:
            if cargando or not outra_parte.value:
                return
            with get_session() as s:
                p = s.get(Persoa, outra_parte.value)
                if p and not (outra_parte_rega.value or "").strip():
                    codigo = p.rega or p.nima or ""
                    if codigo:
                        outra_parte_rega.value = codigo

        outra_parte.select.on_value_change(ao_cambiar_outra_parte)

        with ui.row().classes("w-full no-wrap gap-2"):
            tipo_explotacion = ui.input(
                "Tipo de explotación",
                placeholder="Ex. Bovino de leite, Porcina...",
            ).classes("col")
            tipo_animais = ui.select(
                ESPECIES,
                label="Tipo de animais (especie)",
                value="01",
                with_input=True,
            ).classes("col")

        material = ui.select(
            materiais_cat,
            label="Material",
            value=next(iter(materiais_cat), "5"),
            with_input=True,
        ).classes("w-full")

        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col")
            unidade = ui.select(
                {"t": "t (toneladas)", "m3": "m³ (metros cúbicos)"},
                label="Unidade",
                value="t",
            ).classes("col")

        ui.label("Composición agronómica (% sobre materia fresca):").classes(
            "text-caption text-weight-bold q-mt-sm"
        )
        with ui.row().classes("w-full no-wrap gap-2"):
            n_total = ui.input("N total (%)").classes("col")
            p2o5 = ui.input("P₂O₅ (%)").classes("col")
            k2o = ui.input("K₂O (%)").classes("col")
            materia_organica = ui.input("Materia orgánica (%)").classes("col")

        orixes_opcions = {"": "Non indicada", **ORIXES_COMPOSICION}
        orixe_composicion = ui.select(
            orixes_opcions,
            label="Orixe da composición",
            value="",
        ).classes("w-full")

        parcelas_destino = ui.input(
            "Parcelas de destino",
            placeholder="Opcional: onde se vai aplicar",
        ).classes("w-full")

        with ui.row().classes("w-full no-wrap gap-2"):
            quen = ui.select(persoas_quen, label="Quen o fixo", clearable=True).classes("col")
            horas = ui.input("Horas").classes("col")

        notas = ui.input("Notas").classes("w-full")

        def gardar() -> None:
            with get_session() as session_g:
                actor_actual = usuario_actual(session_g)
                if actor_actual is None:
                    pechar_sesion()
                    return

                def accion() -> None:
                    data_val = parsear_data(data.value)
                    if data_val is None:
                        raise OperacionNonPermitidaError("Indica a data")
                    if not outra_parte.value:
                        raise OperacionNonPermitidaError(
                            "Escolle a outra parte (persoa ou entidade)"
                        )
                    cant_val = parsear_decimal(cantidade.value)
                    if cant_val is None or cant_val <= 0:
                        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")

                    n_val = parsear_decimal(n_total.value)
                    p_val = parsear_decimal(p2o5.value)
                    k_val = parsear_decimal(k2o.value)
                    mo_val = parsear_decimal(materia_organica.value)
                    horas_val = parsear_decimal(horas.value)
                    orixe_val = orixe_composicion.value or None
                    rega_val = (outra_parte_rega.value or "").strip() or None
                    explotacion_val = (tipo_explotacion.value or "").strip()
                    animais_val = tipo_animais.value or ""
                    mat_val = material.value or ""
                    unidade_val = unidade.value or "t"
                    destino_val = (parcelas_destino.value or "").strip() or None
                    notas_val = (notas.value or "").strip() or None

                    if editando["id"] is None:
                        novo = crear_movemento(
                            session_g,
                            actor_actual,
                            horta_id,
                            tipo=tipo.value,
                            data=data_val,
                            outra_parte_id=outra_parte.value,
                            tipo_explotacion=explotacion_val,
                            tipo_animais=animais_val,
                            material=mat_val,
                            cantidade=cant_val,
                            unidade=unidade_val,
                            outra_parte_rega=rega_val,
                            n_total=n_val,
                            p2o5=p_val,
                            k2o=k_val,
                            materia_organica=mo_val,
                            orixe_composicion=orixe_val,
                            parcelas_destino=destino_val,
                            notas=notas_val,
                            persoa_id=quen.value,
                            horas=horas_val,
                        )
                        rematar_tarefa(session_g, actor_actual, editando["tarefa"], novo)
                    else:
                        existente = session_g.get(MovementoEsterco, editando["id"])
                        if existente is not None:
                            actualizar_movemento(
                                session_g,
                                actor_actual,
                                existente,
                                tipo=tipo.value,
                                data=data_val,
                                outra_parte_id=outra_parte.value,
                                tipo_explotacion=explotacion_val,
                                tipo_animais=animais_val,
                                material=mat_val,
                                cantidade=cant_val,
                                unidade=unidade_val,
                                outra_parte_rega=rega_val,
                                n_total=n_val,
                                p2o5=p_val,
                                k2o=k_val,
                                materia_organica=mo_val,
                                orixe_composicion=orixe_val,
                                parcelas_destino=destino_val,
                                notas=notas_val,
                                persoa_id=quen.value,
                                horas=horas_val,
                            )

                ok = executar_accion(session_g, accion)
            if ok:
                dialogo.close()
                recargar_apuntado("movemento_esterco", data.value)

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    def abrir(mov: MovementoEsterco | None = None, tarefa: Tarefa | None = None) -> None:
        nonlocal cargando
        cargando = True
        try:
            editando["id"] = mov.id if mov else None
            editando["tarefa"] = tarefa.id if tarefa else None
            titulo.text = "Editar cesión ou recepción" if mov else "Nova cesión ou recepción"
            outra_parte._cargar()
            tipo.value = mov.tipo if mov else "cesion"
            data.value = (mov.data if mov else date.today()).isoformat()
            outra_parte.value = mov.outra_parte_id if mov else None
            outra_parte_rega.value = (mov.outra_parte_rega or "") if mov else ""
            tipo_explotacion.value = mov.tipo_explotacion if mov else ""
            if mov:
                tipo_animais.value = (
                    mov.tipo_animais
                    if mov.tipo_animais in ESPECIES
                    else next(
                        (k for k, v in ESPECIES.items() if v == mov.tipo_animais),
                        "01",
                    )
                )
            else:
                tipo_animais.value = "01"
            material.value = (
                mov.material if mov and mov.material in materiais_cat
                else next(iter(materiais_cat), "5")
            )
            cantidade.value = f"{mov.cantidade:g}" if mov else ""
            unidade.value = mov.unidade if mov else "t"
            n_total.value = f"{mov.n_total:g}" if mov and mov.n_total is not None else ""
            p2o5.value = f"{mov.p2o5:g}" if mov and mov.p2o5 is not None else ""
            k2o.value = f"{mov.k2o:g}" if mov and mov.k2o is not None else ""
            materia_organica.value = (
                f"{mov.materia_organica:g}" if mov and mov.materia_organica is not None else ""
            )
            orixe_composicion.value = (
                mov.orixe_composicion if mov and mov.orixe_composicion in ORIXES_COMPOSICION
                else ""
            )
            parcelas_destino.value = (mov.parcelas_destino or "") if mov else ""
            notas.value = (mov.notas or "") if mov else ""
            with get_session() as s:
                actor_prop = usuario_actual(s)
                quen_prop = (
                    mov.persoa_id
                    if mov
                    else (proposta_quen(s, actor_prop, horta_id) if actor_prop else None)
                )
            quen.value = quen_prop if quen_prop in persoas_quen else None
            horas.value = f"{mov.horas:g}" if mov and mov.horas is not None else ""
        finally:
            cargando = False
        dialogo.open()

    return abrir


def seccion_estercos(horta_id: int, pode_editar: bool) -> None:
    """Pantalla de xestión de movementos de esterco e purín."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        ano_actual = date.today().year
        resumo = resumo_ano(session, actor, horta_id, ano_actual)
        movementos = listar_movementos(session, actor, horta_id)
        materiais_todos = {
            v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
            for v in valores_vixentes(session, "material_fertilizante")
        }
        nomes_persoas = {
            p.id: nome_completo(p)
            for p in listar_persoas(session, actor, horta_id, so_activas=False)
        }

    with ui.column().classes("tarxeta w-full gap-2 q-mb-md"):
        ui.label(f"Resumo de esterco e purín ({resumo.ano})").classes(
            "text-subtitle1 text-weight-bold"
        )
        if not resumo.cedidos and not resumo.recibidos:
            ui.label("Sen movementos de esterco nin purín neste ano.").classes("texto-suave")
        else:
            with ui.row().classes("w-full gap-4"):
                with ui.column().classes("col gap-1"):
                    ui.label("Cedido").classes("text-weight-bold")
                    if resumo.cedidos:
                        for (mat, uni), cant in resumo.cedidos.items():
                            mat_desc = materiais_todos.get(mat, mat)
                            ui.label(f"• {texto_resumo_material(mat_desc, cant, uni)}")
                        ui.label(
                            f"Total N cedido: {texto_resumo_n(resumo.kg_n_cedido)}"
                        ).classes("text-caption text-weight-bold")
                    else:
                        ui.label("Ningún").classes("texto-suave")
                with ui.column().classes("col gap-1"):
                    ui.label("Recibido").classes("text-weight-bold")
                    if resumo.recibidos:
                        for (mat, uni), cant in resumo.recibidos.items():
                            mat_desc = materiais_todos.get(mat, mat)
                            ui.label(f"• {texto_resumo_material(mat_desc, cant, uni)}")
                        ui.label(
                            f"Total N recibido: {texto_resumo_n(resumo.kg_n_recibido)}"
                        ).classes("text-caption text-weight-bold")
                    else:
                        ui.label("Ningún").classes("texto-suave")
            if resumo.aviso_m3:
                ui.label(resumo.nota_m3).classes("text-caption texto-suave")

    filas = []
    for m in movementos:
        mat_desc = materiais_todos.get(m.material) or m.material
        outra_nome = nomes_persoas.get(m.outra_parte_id, "")
        faltas = faltas_documento(m)
        filas.append({
            "id": m.id,
            "tipo_clave": m.tipo,
            "data": f"{m.data:%d/%m/%Y}",
            "tipo": texto_tipo_movemento(m.tipo),
            "outra_parte": outra_nome,
            "material": mat_desc,
            "cantidade": f"{m.cantidade:g} {m.unidade}",
            "n_total": f"{m.n_total:g} %" if m.n_total is not None else "",
            "orixe_composicion": ORIXES_COMPOSICION.get(
                m.orixe_composicion or "", m.orixe_composicion or ""
            ),
            "faltas": texto_faltas_documento(faltas),
        })

    taboa = (
        ui.table(
            columns=COLUMNAS_TABOA,
            rows=filas,
            row_key="id",
            selection="single",
        )
        .classes("w-full taboa so-ordenador")
        .props(
            'flat bordered '
            'no-data-label="Aínda non hai movementos de esterco nin purín" '
            f"{TEXTOS_TABOA}"
        )
    )

    taboa.add_slot(
        "body-cell-faltas",
        r"""
        <q-td :props="props" class="text-warning">
            {{ props.value }}
        </q-td>
        """,
    )

    doc_mov_id: dict[str, int | None] = {"id": None}
    with (
        ui.dialog().props("persistent") as dialogo_doc,
        ui.card().style("width: min(28rem, 94vw)"),
    ):
        ui.label("Documento do anexo VII").classes("text-h6")
        ui.label(
            "Documento de acompañamento do esterco (RD 1051/2022, anexo VII punto 1)."
        ).classes("text-caption")
        formato = selector_formato()

        def facer_descarga() -> None:
            if not doc_mov_id["id"]:
                return
            with get_session() as session_doc:
                actor_doc = usuario_actual(session_doc)
                if actor_doc is None:
                    pechar_sesion()
                    return
                try:
                    mov = session_doc.get(MovementoEsterco, doc_mov_id["id"])
                    if mov is None or mov.tipo != "cesion":
                        ui.notify(
                            "O documento só se pode xerar para cesións",
                            type="negative",
                        )
                        return
                    datos = documento_anexo_vii(session_doc, actor_doc, mov.id)
                    data_str = f"{mov.data:%Y%m%d}"
                    mov_id = mov.id
                except OperacionNonPermitidaError as erro:
                    ui.notify(str(erro), type="negative")
                    return
            descargar_informe(
                datos,
                formato.value or "xlsx",
                f"anexo-vii-esterco-{mov_id}-{data_str}",
                "Documento de acompañamento do esterco",
                "anexo_vii",
            )
            dialogo_doc.close()

        with ui.row():
            ui.button("Descargar", icon="download", on_click=facer_descarga)
            ui.button("Cancelar", on_click=dialogo_doc.close).props("flat")

    def abrir_anexo_vii() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un movemento na táboa", type="warning")
            return
        fila = taboa.selected[0]
        if fila.get("tipo_clave") != "cesion":
            ui.notify(
                "O documento do anexo VII só se pode xerar para cesións",
                type="warning",
            )
            return
        doc_mov_id["id"] = fila["id"]
        dialogo_doc.open()

    abrir = dialogo_esterco(horta_id) if pode_editar else None

    def editar() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un movemento na táboa", type="warning")
            return
        if not pode_editar or abrir is None:
            return
        mov_id = taboa.selected[0]["id"]
        with get_session() as session_ed:
            m = session_ed.get(MovementoEsterco, mov_id)
            if m is not None:
                abrir(m)

    def dar_de_baixa() -> None:
        if not taboa.selected:
            ui.notify("Escolle primeiro un movemento na táboa", type="warning")
            return
        mov_id = taboa.selected[0]["id"]

        def confirmar() -> None:
            with get_session() as session_b:
                actor_b = usuario_actual(session_b)
                m = session_b.get(MovementoEsterco, mov_id)
                if actor_b is None or m is None:
                    return
                ok = executar_accion(
                    session_b,
                    lambda: dar_de_baixa_movemento(session_b, actor_b, m),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa este movemento de esterco? Non se borra: consérvase no histórico.",
            confirmar,
        )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    if pode_editar and abrir is not None:
        accions_tarxeta.append(("Editar", "edit", editar))
    accions_tarxeta.append(("Documento do anexo VII", "description", abrir_anexo_vii))
    if pode_editar:
        accions_tarxeta.append(("Dar de baixa", "archive", dar_de_baixa))

    tarxetas_da_taboa(taboa, "data", ["tipo", "material", "cantidade"], accions_tarxeta)

    with ui.row():
        if pode_editar and abrir is not None:
            ui.button(
                "Nova cesión ou recepción",
                icon="add",
                on_click=lambda: abrir(None),
            )
            with ui.row().classes("so-ordenador"):
                ui.button("Editar", icon="edit", on_click=editar).props("outline")
                ui.button(
                    "Documento do anexo VII",
                    icon="description",
                    on_click=abrir_anexo_vii,
                ).props("outline")
                ui.button(
                    "Dar de baixa",
                    icon="archive",
                    on_click=dar_de_baixa,
                ).props("outline")
        else:
            with ui.row().classes("so-ordenador"):
                ui.button(
                    "Documento do anexo VII",
                    icon="description",
                    on_click=abrir_anexo_vii,
                ).props("outline")
