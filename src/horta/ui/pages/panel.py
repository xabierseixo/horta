"""Páxina do panel de explotacións (paso 168): vista conxunta de todas as explotacións."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.models.usuario import RolGlobal
from horta.services.panel import ResumoExplotacion, resumo_explotacions
from horta.ui.lista_tarxetas import lista_tarxetas
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_PAPEIS: dict[str, str] = {
    "admin": "Administración",
    "editor": "Edición",
    "lector": "Só mirar",
}


@ui.page("/panel")
def panel_page() -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        e_admin_global = actor.rol == RolGlobal.ADMIN
        resumos = resumo_explotacions(session, actor)

    cabeceira_paxina(mostrar_admin=e_admin_global)
    ui.label("As miñas explotacións").classes("text-h6")

    if not resumos:
        ui.label("Aínda non tes ningunha explotación").classes("texto-suave q-mt-md")
        return

    total_explotacions = len(resumos)
    con_avisos = sum(1 for r in resumos if r.total_avisos > 0)
    palabra_explotacion = "explotación" if total_explotacions == 1 else "explotacións"
    ui.label(
        f"{total_explotacions} {palabra_explotacion} · {con_avisos} con avisos"
    ).classes("texto-suave q-mb-md")

    columnas = [
        {"name": "nome", "label": "Explotación", "field": "nome", "align": "left"},
        {"name": "papel", "label": "Papel", "field": "papel", "align": "left"},
        {"name": "avisos", "label": "Avisos", "field": "avisos", "align": "right"},
        {"name": "en_regra", "label": "En regra", "field": "en_regra", "align": "right"},
        {"name": "documentos", "label": "Documentos", "field": "documentos", "align": "right"},
        {"name": "caderno", "label": "Caderno", "field": "caderno", "align": "right"},
        {
            "name": "tarefas_atrasadas",
            "label": "Tarefas atrasadas",
            "field": "tarefas_atrasadas",
            "align": "right",
        },
        {
            "name": "ultimo_traballo",
            "label": "Último traballo",
            "field": "ultimo_traballo",
            "align": "left",
        },
    ]

    filas = [
        {
            "id": r.horta_id,
            "nome": r.nome,
            "papel": _PAPEIS.get(r.rol, r.rol),
            "avisos": r.total_avisos,
            "en_regra": r.requisitos_pendentes,
            "documentos": r.documentos_aviso,
            "caderno": r.faltas_caderno,
            "tarefas_atrasadas": r.tarefas_atrasadas,
            "ultimo_traballo": (
                f"{r.ultimo_traballo:%d/%m/%Y}" if r.ultimo_traballo else "—"
            ),
        }
        for r in resumos
    ]

    def ao_escoller(e: Any) -> None:
        seleccionados = getattr(e, "selection", None) or taboa.selected
        if seleccionados:
            ui.navigate.to(f"/hortas/{seleccionados[0]['id']}/resumo")

    taboa = (
        ui.table(
            columns=columnas,
            rows=filas,
            row_key="id",
            selection="single",
            on_select=ao_escoller,
        )
        .classes("w-full taboa so-ordenador")
        .props(f'flat bordered no-data-label="Aínda non tes ningunha explotación" {TEXTOS_TABOA}')
    )
    taboa.on("rowClick", lambda msg: ui.navigate.to(f"/hortas/{msg.args[1]['id']}/resumo"))

    taboa.add_slot(
        "body-cell-avisos",
        """
        <q-td :props="props">
            <span :class="props.value > 0 ? 'text-warning text-weight-bold' : ''">
                {{ props.value }}
            </span>
        </q-td>
        """,
    )

    elementos = [
        (
            r.horta_id,
            r.nome,
            (
                f"{r.total_avisos} avisos · último traballo "
                + (f"{r.ultimo_traballo:%d/%m/%Y}" if r.ultimo_traballo else "—")
            ),
        )
        for r in resumos
    ]
    lista_tarxetas(
        elementos,
        ao_tocar=lambda horta_id: ui.navigate.to(f"/hortas/{horta_id}/resumo"),
        baleiro="Aínda non tes ningunha explotación",
    )
