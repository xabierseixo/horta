"""Sección de recomendacións do asesor fitosanitario (mellora N7)."""

from __future__ import annotations

from collections.abc import Callable

from nicegui import ui

from horta.db import get_session
from horta.models.recomendacion import Recomendacion
from horta.models.tratamento_fito import TratamentoFito
from horta.services.catalogos import describir
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.persoas import listar_persoas
from horta.services.recomendacions import (
    avisos_recomendacion,
    dar_de_baixa_recomendacion,
    descartar_recomendacion,
    listar_recomendacions,
)
from horta.ui.accions import executar_accion
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.lista_tarxetas import tarxetas_da_taboa
from horta.ui.numeros import texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA


def texto_aviso_recomendacions(n: int) -> str:
    """Texto do aviso en Inicio cando hai recomendacións pendentes."""
    palabra = "recomendación" if n == 1 else "recomendacións"
    return f"O asesor deixou {n} {palabra} por aplicar"


def texto_ligazon_recomendacions(n: int) -> str:
    """Texto da ligazón dende Tratamentos cara a Recomendacións."""
    return f"Recomendacións do asesor ({n} pendentes)"


def texto_estado_recomendacion(estado: str) -> str:
    """Etiqueta lexible para o estado dunha recomendación."""
    return {
        "pendente": "Pendente",
        "aplicada": "Aplicada",
        "descartada": "Descartada",
    }.get(estado, estado)


def seccion_recomendacions(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        recs = listar_recomendacions(session, actor, horta_id)
        persoas = {
            p.id: p.nome
            for p in listar_persoas(session, actor, horta_id, so_activas=False)
        }
        cultivos_horta = {
            c.id: nome_cultivo(c)
            for c in listar_cultivos(session, actor, horta_id)
        }
        filas = []
        for r in recs:
            c_nomes = [
                cultivos_horta.get(int(c.get("cultivo_id") or 0), "")
                for c in (r.cultivos or [])
            ]
            p_nomes = [
                describir(session, p.get("tipo", ""), p.get("codigo", ""))
                for p in (r.problemas or [])
            ]
            prod_nomes = [
                p.get("nome_comercial") or p.get("num_rexistro") or ""
                for p in (r.produtos or [])
            ]
            avisos_lista = (
                avisos_recomendacion(session, r) if r.estado == "pendente" else []
            )
            filas.append({
                "id": r.id,
                "estado_clave": r.estado,
                "data": texto_data(r.data),
                "valida_ata": texto_data(r.valida_ata) if r.valida_ata else "",
                "cultivos": ", ".join(n for n in c_nomes if n),
                "problema": ", ".join(n for n in p_nomes if n),
                "produtos": ", ".join(n for n in prod_nomes if n),
                "asesor": persoas.get(r.asesor_persoa_id, ""),
                "estado": texto_estado_recomendacion(r.estado),
                "avisos": " · ".join(avisos_lista),
            })

    opcions_filtro = {
        "pendente": "Pendentes",
        "aplicada": "Aplicadas",
        "descartada": "Descartadas",
        "todas": "Todas",
    }
    with ui.row().classes("w-full items-center justify-between q-mb-sm"):
        filtro_estado = ui.select(
            opcions_filtro,
            value="pendente",
            label="Estado",
        ).classes("w-48")

    taboa = ui.table(
        columns=[
            {"name": "data", "label": "Data", "field": "data", "align": "left"},
            {
                "name": "valida_ata",
                "label": "Válida ata",
                "field": "valida_ata",
                "align": "left",
            },
            {
                "name": "cultivos",
                "label": "Cultivos",
                "field": "cultivos",
                "align": "left",
            },
            {
                "name": "problema",
                "label": "Problema",
                "field": "problema",
                "align": "left",
            },
            {
                "name": "produtos",
                "label": "Produtos",
                "field": "produtos",
                "align": "left",
            },
            {"name": "asesor", "label": "Asesor", "field": "asesor", "align": "left"},
            {"name": "estado", "label": "Estado", "field": "estado", "align": "left"},
            {"name": "avisos", "label": "Avisos", "field": "avisos", "align": "left"},
        ],
        rows=[f for f in filas if f["estado_clave"] == "pendente"],
        row_key="id",
        selection="single" if pode_editar else None,
    ).classes("w-full taboa so-ordenador").props(
        f'flat bordered no-data-label="Non hai recomendacións que amosar" {TEXTOS_TABOA}'
    )

    accions_tarxeta: list[tuple[str, str, Callable[[], None]]] = []
    refrescar_tarxetas = tarxetas_da_taboa(
        taboa, "data", ["cultivos", "problema", "estado"], accions_tarxeta
    )

    def aplicar_filtro() -> None:
        escolla = filtro_estado.value
        taboa.selected = []
        if escolla == "todas":
            taboa.rows = filas
        else:
            taboa.rows = [f for f in filas if f["estado_clave"] == escolla]
        refrescar_tarxetas.refresh()

    filtro_estado.on_value_change(aplicar_filtro)

    if not pode_editar:
        return

    # Aquí e non arriba: tratamentos.py importa este módulo para a súa ligazón
    from horta.ui.pages.tratamentos import dialogo_tratamento_fito

    abrir = dialogo_tratamento_fito(horta_id)

    def seleccionado() -> int | None:
        if not taboa.selected:
            ui.notify("Selecciona unha recomendación na táboa", type="warning")
            return None
        return int(taboa.selected[0]["id"])

    def aplicar() -> None:
        rec_id = seleccionado()
        if rec_id is None:
            return
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            rec = session.get(Recomendacion, rec_id)
            if rec is None or rec.estado != "pendente":
                ui.notify("Só se poden aplicar recomendacións pendentes", type="warning")
                return
            abrir(recomendacion=rec, modo="tratamento")

    def editar() -> None:
        rec_id = seleccionado()
        if rec_id is None:
            return
        with get_session() as session:
            actor_actual = usuario_actual(session)
            if actor_actual is None:
                pechar_sesion()
                return
            rec = session.get(Recomendacion, rec_id)
            if rec is None or rec.estado != "pendente":
                ui.notify("Só se poden editar recomendacións pendentes", type="warning")
                return
            abrir(recomendacion=rec, modo="recomendacion")

    with ui.dialog() as dialogo_descarte, ui.card().style("width: min(28rem, 94vw)"):
        ui.label("Descartar recomendación").classes("text-h6")
        motivo_input = ui.input("Motivo do descarte").classes("w-full")

        def confirmar_descarte() -> None:
            motivo = motivo_input.value.strip()
            if not motivo:
                ui.notify("Indica o motivo do descarte", type="warning")
                return
            rec_id = seleccionado()
            if rec_id is None:
                return
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                rec = session.get(Recomendacion, rec_id)
                if rec is None:
                    return
                ok = executar_accion(
                    session,
                    lambda: descartar_recomendacion(session, actor_actual, rec, motivo),
                )
            if ok:
                dialogo_descarte.close()
                ui.navigate.reload()

        with ui.row():
            ui.button("Descartar", icon="cancel", on_click=confirmar_descarte).props(
                "color=negative"
            )
            ui.button("Cancelar", on_click=dialogo_descarte.close).props("flat")

    def pedir_descarte() -> None:
        rec_id = seleccionado()
        if rec_id is None:
            return
        with get_session() as session:
            rec = session.get(Recomendacion, rec_id)
            if rec is None or rec.estado != "pendente":
                ui.notify("Só se poden descartar recomendacións pendentes", type="warning")
                return
        motivo_input.value = ""
        dialogo_descarte.open()

    def ver_tratamento() -> None:
        rec_id = seleccionado()
        if rec_id is None:
            return
        with get_session() as session:
            rec = session.get(Recomendacion, rec_id)
            if rec is None or rec.estado != "aplicada" or not rec.tratamento_id:
                ui.notify("Esta recomendación non ten tratamento aplicado", type="warning")
                return
            tratamento = session.get(TratamentoFito, rec.tratamento_id)
            if tratamento is not None:
                abrir(tratamento)

    def dar_de_baixa() -> None:
        rec_id = seleccionado()
        if rec_id is None:
            return

        def confirmar() -> None:
            with get_session() as session:
                actor_actual = usuario_actual(session)
                if actor_actual is None:
                    pechar_sesion()
                    return
                rec = session.get(Recomendacion, rec_id)
                if rec is None:
                    return
                ok = executar_accion(
                    session,
                    lambda: dar_de_baixa_recomendacion(session, actor_actual, rec),
                )
            if ok:
                ui.navigate.reload()

        confirmar_eliminacion(
            "Dar de baixa esta recomendación? Consérvase no histórico pero deixa de "
            "aparecer na lista.",
            confirmar,
        )

    accions_tarxeta.extend([
        ("Aplicar", "check_circle", aplicar),
        ("Editar", "edit", editar),
        ("Descartar", "cancel", pedir_descarte),
        ("Ver o tratamento", "visibility", ver_tratamento),
        ("Dar de baixa", "archive", dar_de_baixa),
    ])

    with ui.row().classes("gap-2 items-center"):
        ui.button(
            "Nova recomendación",
            icon="add",
            on_click=lambda: abrir(modo="recomendacion"),
        )
        with ui.row().classes("so-ordenador gap-2"):
            ui.button("Aplicar", icon="check_circle", on_click=aplicar).props("outline")
            ui.button("Editar", icon="edit", on_click=editar).props("outline")
            ui.button("Descartar", icon="cancel", on_click=pedir_descarte).props("outline")
            ui.button(
                "Ver o tratamento",
                icon="visibility",
                on_click=ver_tratamento,
            ).props("outline")
            ui.button("Dar de baixa", icon="archive", on_click=dar_de_baixa).props("outline")


__all__ = [
    "seccion_recomendacions",
    "texto_aviso_recomendacions",
    "texto_estado_recomendacion",
    "texto_ligazon_recomendacions",
]
