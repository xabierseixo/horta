"""Páxina do panel de explotacións (paso 168): vista conxunta de todas as explotacións."""

from __future__ import annotations

from typing import Any

from nicegui import ui

from horta.db import get_session
from horta.idiomas import N_, _, ngettext
from horta.models.usuario import RolGlobal
from horta.services.panel import resumo_explotacions
from horta.ui.lista_tarxetas import lista_tarxetas
from horta.ui.nav import cabeceira_paxina
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA

_PAPEIS: dict[str, str] = {
    "admin": N_("Administración"),
    "editor": N_("Edición"),
    "lector": N_("Só mirar"),
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
    ui.label(_("As miñas explotacións")).classes("text-h6")

    if not resumos:
        ui.label(_("Aínda non tes ningunha explotación")).classes("texto-suave q-mt-md")
        return

    total_explotacions = len(resumos)
    con_avisos = sum(1 for r in resumos if r.total_avisos > 0)
    ui.label(
        ngettext(
            "{n} explotación · {con_avisos} con avisos",
            "{n} explotacións · {con_avisos} con avisos",
            total_explotacions,
        ).format(n=total_explotacions, con_avisos=con_avisos)
    ).classes("texto-suave q-mb-md")

    columnas = [
        {"name": "nome", "label": _("Explotación"), "field": "nome", "align": "left"},
        {"name": "papel", "label": _("Papel"), "field": "papel", "align": "left"},
        {"name": "avisos", "label": _("Avisos"), "field": "avisos", "align": "right"},
        {"name": "en_regra", "label": _("En regra"), "field": "en_regra", "align": "right"},
        {"name": "documentos", "label": _("Documentos"), "field": "documentos", "align": "right"},
        {"name": "caderno", "label": _("Caderno"), "field": "caderno", "align": "right"},
        {
            "name": "tarefas_atrasadas",
            "label": _("Tarefas atrasadas"),
            "field": "tarefas_atrasadas",
            "align": "right",
        },
        {
            "name": "ultimo_traballo",
            "label": _("Último traballo"),
            "field": "ultimo_traballo",
            "align": "left",
        },
    ]

    filas = [
        {
            "id": r.horta_id,
            "nome": r.nome,
            "papel": _(_PAPEIS[r.rol]) if r.rol in _PAPEIS else r.rol,
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
        .props(
            f'flat bordered no-data-label="{_("Aínda non tes ningunha explotación")}" '
            f"{TEXTOS_TABOA}"
        )
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
            _("{total_avisos} avisos · último traballo {data}").format(
                total_avisos=r.total_avisos,
                data=f"{r.ultimo_traballo:%d/%m/%Y}" if r.ultimo_traballo else "—",
            ),
        )
        for r in resumos
    ]
    lista_tarxetas(
        elementos,
        ao_tocar=lambda horta_id: ui.navigate.to(f"/hortas/{horta_id}/resumo"),
        baleiro=_("Aínda non tes ningunha explotación"),
    )
