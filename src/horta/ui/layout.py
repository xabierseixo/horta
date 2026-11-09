"""Marco común das páxinas dunha horta: menú lateral, cabeceira móbil e cabeceira de sección."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from nicegui import ui

from horta.idiomas import N_, _
from horta.ui.accions import mostrar_aviso_pendente
from horta.ui.sesion import pechar_sesion
from horta.ui.tema import aplicar_tema


def _version() -> str:
    """A versión que está a funcionar (o último cambio gardado), para saber que se está a ver."""
    try:
        return subprocess.run(
            ["git", "log", "-1", "--format=%h · %cd", "--date=format:%d/%m %H:%M"],
            cwd=Path(__file__).parent, capture_output=True, text=True, timeout=5,
        ).stdout.strip() or "?"
    except OSError:
        return "?"


VERSION = _version()


@dataclass(frozen=True)
class Seccion:
    clave: str
    etiqueta: str
    icona: str  # Material Icons
    grupo: str | None
    so_admin_horta: bool = False
    no_menu: bool = False


SECCIONS: tuple[Seccion, ...] = (
    Seccion("resumo", N_("Inicio"), "home", None),
    Seccion("diario", N_("Diario"), "event_note", None),
    Seccion("calendario", N_("Calendario"), "calendar_month", None),
    Seccion("informes", N_("Informes"), "description", None),
    Seccion("estatisticas", N_("Estatísticas"), "bar_chart", None),
    # Menú por áreas (deseño global §2bis e §2ter)
    Seccion("parcelas", N_("Parcelas"), "map", N_("Produción")),
    Seccion("mapa", N_("Mapa das terras"), "public", N_("Produción")),
    Seccion("cultivos", N_("Cultivos"), "spa", N_("Produción")),
    Seccion("animais", N_("Animais"), "pets", N_("Produción")),
    Seccion("sensores", N_("Sensores"), "sensors", N_("Produción")),
    Seccion("equipo", N_("Equipo"), "groups", N_("Xestión")),
    Seccion("contactos", N_("Contactos"), "contacts", N_("Xestión")),
    Seccion("maquinaria", N_("Maquinaria"), "agriculture", N_("Xestión")),
    Seccion("instalacions", N_("Instalacións"), "warehouse", N_("Xestión")),
    Seccion("produtos", N_("Produtos"), "shopping_basket", N_("Xestión")),
    Seccion("lotes", N_("Lotes"), "inventory", N_("Xestión")),
    Seccion("cartos", N_("Contas"), "euro", N_("Xestión")),
    Seccion("documentos", N_("Documentos"), "folder_shared", N_("Xestión")),
    Seccion("plan", N_("Plan de empresa"), "business_center", N_("Explotación")),
    Seccion("certificacions", N_("Certificacións"), "verified", N_("Explotación")),
    Seccion(
        "explotacion",
        N_("Datos da explotación"),
        "store",
        N_("Explotación"),
        so_admin_horta=True,
    ),
    # A táboa de cada tipo de traballo: fóra do menú, chégase desde o Diario
    Seccion("tratamentos", N_("Tratamentos"), "sanitizer", None, no_menu=True),
    Seccion(
        "recomendacions",
        N_("Recomendacións da persoa asesora"),
        "assignment",
        None,
        no_menu=True,
    ),
    Seccion("pragas", N_("Seguimento de pragas"), "bug_report", None, no_menu=True),
    Seccion("visitas", N_("Visitas técnicas"), "person_pin_circle", None, no_menu=True),
    Seccion("fertilizacion", N_("Abonados"), "compost", None, no_menu=True),
    Seccion("estercos", N_("Estercos e purín"), "compost", None, no_menu=True),
    Seccion("rega", N_("Regas"), "water_drop", None, no_menu=True),
    Seccion("labores", N_("Labores"), "grass", None, no_menu=True),
    Seccion("analises", N_("Tomas de mostras"), "science", None, no_menu=True),
    Seccion("colleitas", N_("Colleitas"), "inventory_2", None, no_menu=True),
    Seccion("coidados", N_("Coidados dos animais"), "pets", None, no_menu=True),
    Seccion(
        "movementos",
        N_("Entradas e saídas de animais"),
        "swap_horiz",
        None,
        no_menu=True,
    ),
    Seccion("producion", N_("Produción dos animais"), "egg", None, no_menu=True),
    Seccion("pastoreo", N_("Pastoreo"), "landscape", None, no_menu=True),
    Seccion("tarefas", N_("Tarefas"), "task_alt", None, no_menu=True),
)
_CLAVES = {s.clave for s in SECCIONS}
NOVA_EXPLOTACION = -1  # valor especial do selector de explotación


def url_seccion(horta_id: int, clave: str) -> str:
    return f"/hortas/{horta_id}/{clave}"


def normalizar_seccion(clave: str) -> str:
    return clave if clave in _CLAVES else "resumo"


def seccions_visibles(e_horta_admin: bool) -> list[Seccion]:
    """As do menú: as táboas de cada tipo de traballo ábrense desde o Diario."""
    return [s for s in SECCIONS if (e_horta_admin or not s.so_admin_horta) and not s.no_menu]


def marco_horta(
    *,
    horta_id: int,
    seccion: str,
    hortas: dict[int, str],
    nome_usuario: str,
    e_horta_admin: bool,
    e_admin_global: bool,
) -> None:
    """Debuxa o menú lateral e a cabeceira móbil. O contido da páxina vai despois."""
    aplicar_tema()
    mostrar_aviso_pendente()
    menu = ui.left_drawer(value=False, fixed=True).props(
        'show-if-above :width="248" :breakpoint="1024"'
    ).classes("menu-lateral q-pa-md")

    with ui.header().classes("cabeceira-mobil lt-md items-center q-py-xs"):
        ui.button(icon="menu", on_click=menu.toggle).props(
            f'flat round color=white aria-label="{_("Abrir menú")}"'
        )
        ui.label(hortas.get(horta_id, "AgroXest360")).classes("text-white text-subtitle1")

    with menu:
        with ui.column().classes("w-full gap-1 no-wrap").style("min-height: 100%"):
            with ui.link(target="/").classes("menu-marca"):
                ui.icon("eco", color="green-3").classes("text-h5")
                ui.label("AgroXest360")
            if len(hortas) >= 2:
                with ui.link(target="/panel").classes("menu-item w-full"):
                    ui.icon("dashboard").classes("text-h6")
                    ui.label(_("Todas as explotacións"))
            ui.select(
                {**hortas, NOVA_EXPLOTACION: _("+ Nova explotación")},
                value=horta_id,
                label=_("Explotación"),
                on_change=lambda e: ui.navigate.to(
                    "/?nova=1" if e.value == NOVA_EXPLOTACION else url_seccion(e.value, seccion)
                ),
            ).props("dense outlined dark").classes("menu-selector w-full q-mb-sm")

            grupo_actual: str | None = None
            for s in seccions_visibles(e_horta_admin):
                if s.grupo != grupo_actual and s.grupo is not None:
                    ui.label(_(s.grupo)).classes("menu-grupo")
                grupo_actual = s.grupo
                clases = "menu-item w-full activo" if s.clave == seccion else "menu-item w-full"
                with ui.link(target=url_seccion(horta_id, s.clave)).classes(clases):
                    ui.icon(s.icona).classes("text-h6")
                    ui.label(_(s.etiqueta))

            ui.space()
            with ui.column().classes("menu-pe w-full gap-1"):
                ui.label(nome_usuario).classes("text-white text-weight-bold q-px-sm")
                if e_admin_global:
                    with ui.link(target="/admin/usuarios").classes("menu-item w-full"):
                        ui.icon("admin_panel_settings").classes("text-h6")
                        ui.label(_("Administración"))
                    with ui.link(target="/admin/catalogos").classes("menu-item w-full"):
                        ui.icon("library_books").classes("text-h6")
                        ui.label(_("Catálogos oficiais"))
                    with ui.link(target="/admin/legal").classes("menu-item w-full"):
                        ui.icon("gavel").classes("text-h6")
                        ui.label(_("Datos legais"))
                with ui.link(target="/conta").classes("menu-item w-full"):
                    ui.icon("person").classes("text-h6")
                    ui.label(_("A miña conta"))
                with ui.element("button").props('type="button"').classes(
                    "menu-item w-full menu-boton"
                ).on("click", pechar_sesion):
                    ui.icon("logout").classes("text-h6")
                    ui.label(_("Pechar sesión"))
                ui.label(_("Versión {version}").format(version=VERSION)).classes(
                    "text-caption q-px-sm"
                ).style("color: rgba(255,255,255,.6)")


def cabeceira_seccion(titulo: str, migas: str) -> ui.row:
    """Título da sección; devolve a fila onde se poñen os botóns de acción."""
    with ui.row().classes("w-full items-end justify-between q-mb-md wrap"):
        with ui.column().classes("gap-0"):
            ui.label(_(migas)).classes("migas")
            ui.label(_(titulo)).classes("titulo-seccion")
        accions = ui.row().classes("gap-2 wrap")
    return accions
