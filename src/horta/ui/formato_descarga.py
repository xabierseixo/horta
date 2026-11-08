"""Selector de formato e descarga de informes en varios formatos."""

from __future__ import annotations

from nicegui import ui

from horta.services.formatos import FORMATOS, converter


def selector_formato() -> ui.select:
    """Selector do formato de descarga para informes."""
    return ui.select(FORMATOS, value="xlsx", label="Formato")


def descargar_informe(
    xlsx: bytes, formato: str, nome: str, titulo: str, raiz: str
) -> None:
    """Converte os datos dun informe e lanza a descarga coa extensión axeitada."""
    contido, extension = converter(xlsx, formato, titulo, raiz)
    ui.download.content(contido, f"{nome}.{extension}")
