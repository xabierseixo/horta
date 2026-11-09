"""Texto e icona do botón de confirmar segundo o que se vai facer."""

from __future__ import annotations

from horta.idiomas import N_, _

_CADEAS_BOTOES = (
    N_("Dar de baixa"),
    N_("Xerar"),
    N_("Eliminar"),
)


def boton_para(mensaxe: str) -> tuple[str, str]:
    """«Dar de baixa…» non borra nada: o botón di así. «Xerar…», tampouco. O resto, «Eliminar»."""
    if mensaxe.startswith("Dar de baixa") or mensaxe.startswith(_("Dar de baixa")):
        return _("Dar de baixa"), "archive"
    if mensaxe.startswith("Xerar") or mensaxe.startswith(_("Xerar")):
        return _("Xerar"), "key"
    return _("Eliminar"), "delete"
