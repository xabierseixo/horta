from __future__ import annotations

from nicegui import ui

from horta.ui.sesion import boton_pechar_sesion


def cabeceira_paxina(*, titulo_horta: str | None = None, mostrar_admin: bool = False) -> None:
    """Cabeceira de navegación común a todas as páxinas autenticadas.

    Amosa sempre un enlace a inicio e o botón de pechar sesión; opcionalmente
    o nome da horta actual (como referencia, non coma enlace) e un enlace ao
    panel de administración cando o usuario ten rol global admin.
    """
    with ui.row().classes("w-full items-center q-mb-md"):
        ui.link("🌱 Horta", "/").classes("text-lg font-bold no-underline")
        if titulo_horta is not None:
            ui.label("›").classes("text-grey")
            ui.label(titulo_horta).classes("text-lg")
        ui.space()
        if mostrar_admin:
            ui.link("Administración", "/admin/usuarios")
        boton_pechar_sesion()
    ui.separator()
