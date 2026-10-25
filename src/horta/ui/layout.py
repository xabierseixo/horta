"""Marco común das páxinas dunha horta: menú lateral, cabeceira móbil e cabeceira de sección."""

from __future__ import annotations

from dataclasses import dataclass

from nicegui import ui

from horta.ui.sesion import pechar_sesion
from horta.ui.tema import aplicar_tema


@dataclass(frozen=True)
class Seccion:
    clave: str
    etiqueta: str
    icona: str  # Material Icons
    grupo: str | None
    so_admin_horta: bool = False


SECCIONS: tuple[Seccion, ...] = (
    Seccion("resumo", "Resumo", "dashboard", None),
    Seccion("parcelas", "Parcelas", "map", "Terra"),
    Seccion("cultivos", "Cultivos", "spa", "Terra"),
    Seccion("tratamentos", "Tratamentos", "sanitizer", "Caderno"),
    Seccion("fertilizacion", "Fertilización", "compost", "Caderno"),
    Seccion("rega", "Rega", "water_drop", "Caderno"),
    Seccion("analises", "Análises", "science", "Caderno"),
    Seccion("colleitas", "Colleitas", "inventory_2", "Caderno"),
    Seccion("tarefas", "Tarefas", "task_alt", "Caderno"),
    Seccion("animais", "Animais", "pets", "Gandaría"),
    Seccion("equipo", "Equipo", "groups", "Equipo"),
    Seccion("maquinaria", "Maquinaria", "agriculture", "Equipo"),
)
_CLAVES = {s.clave for s in SECCIONS}
NOVA_EXPLOTACION = -1  # valor especial do selector de explotación


def url_seccion(horta_id: int, clave: str) -> str:
    return f"/hortas/{horta_id}/{clave}"


def normalizar_seccion(clave: str) -> str:
    return clave if clave in _CLAVES else "resumo"


def seccions_visibles(e_horta_admin: bool) -> list[Seccion]:
    return [s for s in SECCIONS if e_horta_admin or not s.so_admin_horta]


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
    menu = ui.left_drawer(value=False, fixed=True).props(
        'show-if-above :width="248" :breakpoint="1024"'
    ).classes("menu-lateral q-pa-md")

    with ui.header().classes("cabeceira-mobil lt-md items-center q-py-xs"):
        ui.button(icon="menu", on_click=menu.toggle).props(
            'flat round color=white aria-label="Abrir menú"'
        )
        ui.label(hortas.get(horta_id, "Horta")).classes("text-white text-subtitle1")

    with menu:
        with ui.column().classes("w-full gap-1 no-wrap").style("min-height: 100%"):
            with ui.link(target="/").classes("menu-marca"):
                ui.icon("eco", color="green-3").classes("text-h5")
                ui.label("Horta")
            ui.select(
                {**hortas, NOVA_EXPLOTACION: "+ Nova explotación"},
                value=horta_id,
                label="Explotación",
                on_change=lambda e: ui.navigate.to(
                    "/?nova=1" if e.value == NOVA_EXPLOTACION else url_seccion(e.value, seccion)
                ),
            ).props("dense outlined dark").classes("menu-selector w-full q-mb-sm")

            grupo_actual: str | None = None
            for s in seccions_visibles(e_horta_admin):
                if s.grupo != grupo_actual and s.grupo is not None:
                    ui.label(s.grupo).classes("menu-grupo")
                grupo_actual = s.grupo
                clases = "menu-item w-full activo" if s.clave == seccion else "menu-item w-full"
                with ui.link(target=url_seccion(horta_id, s.clave)).classes(clases):
                    ui.icon(s.icona).classes("text-h6")
                    ui.label(s.etiqueta)

            ui.space()
            with ui.column().classes("menu-pe w-full gap-1"):
                ui.label(nome_usuario).classes("text-white text-weight-bold q-px-sm")
                if e_admin_global:
                    with ui.link(target="/admin/usuarios").classes("menu-item w-full"):
                        ui.icon("admin_panel_settings").classes("text-h6")
                        ui.label("Administración")
                    with ui.link(target="/admin/catalogos").classes("menu-item w-full"):
                        ui.icon("library_books").classes("text-h6")
                        ui.label("Catálogos oficiais")
                with ui.element("button").props('type="button"').classes(
                    "menu-item w-full menu-boton"
                ).on("click", pechar_sesion):
                    ui.icon("logout").classes("text-h6")
                    ui.label("Pechar sesión")


def cabeceira_seccion(titulo: str, migas: str) -> ui.row:
    """Título da sección; devolve a fila onde se poñen os botóns de acción."""
    with ui.row().classes("w-full items-end justify-between q-mb-md wrap"):
        with ui.column().classes("gap-0"):
            ui.label(migas).classes("migas")
            ui.label(titulo).classes("titulo-seccion")
        accions = ui.row().classes("gap-2 wrap")
    return accions
