from __future__ import annotations

from nicegui import ui

from horta.ui.sesion import boton_pechar_sesion

# Paleta propia da app (verde-horta / terra), en vez do azul xenérico de Quasar.
COR_PRIMARIA = "#4A7856"  # verde folla — accións principais
COR_TEXTO = "#26332B"  # verde moi escuro — texto e "secondary"
COR_NEGATIVA = "#9C4A2E"  # terra/rubio — accións destrutivas (eliminar)
COR_FONDO = "#FAF8F3"  # branco morno


def aplicar_paleta() -> None:
    """Cores da app para o cliente actual. Chamar unha vez por páxina."""
    ui.colors(primary=COR_PRIMARIA, secondary=COR_TEXTO, negative=COR_NEGATIVA, dark=COR_TEXTO)
    ui.query("body").style(f"background-color: {COR_FONDO}")


def cabeceira_paxina(*, titulo_horta: str | None = None, mostrar_admin: bool = False) -> None:
    """Cabeceira de navegación común a todas as páxinas autenticadas.

    Amosa sempre un enlace a inicio e o botón de pechar sesión; opcionalmente
    o nome da horta actual (como referencia, non coma enlace) e un enlace ao
    panel de administración cando o usuario ten rol global admin.
    """
    aplicar_paleta()
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
