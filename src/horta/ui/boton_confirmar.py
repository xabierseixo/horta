"""Texto e icona do botón de confirmar segundo o que se vai facer."""


def boton_para(mensaxe: str) -> tuple[str, str]:
    """«Dar de baixa…» non borra nada: o botón di así. «Xerar…», tampouco. O resto, «Eliminar»."""
    if mensaxe.startswith("Dar de baixa"):
        return "Dar de baixa", "archive"
    if mensaxe.startswith("Xerar"):
        return "Xerar", "key"
    return "Eliminar", "delete"
