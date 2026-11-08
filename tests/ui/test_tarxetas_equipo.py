"""Probas para o detalle das tarxetas de equipo e contactos (funcións puras)."""

from __future__ import annotations

from horta.ui.pages.equipo import detalle_tarxeta_contacto, detalle_tarxeta_equipo


def test_detalle_tarxeta_equipo_completo() -> None:
    """Funcións e data do carné ROPO sepáranse con ' · '."""
    fila = {"funcions": "Administrador, Traballador", "ropo": "20/05/2028"}
    assert detalle_tarxeta_equipo(fila) == "Administrador, Traballador · ROPO ata 20/05/2028"


def test_detalle_tarxeta_equipo_sen_ropo() -> None:
    """Se non ten carné ROPO, só saen as funcións."""
    fila = {"funcions": "Traballador", "ropo": ""}
    assert detalle_tarxeta_equipo(fila) == "Traballador"


def test_detalle_tarxeta_equipo_so_ropo() -> None:
    """Se non ten funcións pero ten carné ROPO, sae só o aviso do carné."""
    fila = {"funcions": "", "ropo": "15/10/2027"}
    assert detalle_tarxeta_equipo(fila) == "ROPO ata 15/10/2027"


def test_detalle_tarxeta_equipo_baleiro() -> None:
    """Se non hai funcións nin carné ROPO, devolve cadea baleira."""
    assert detalle_tarxeta_equipo({}) == ""
    assert detalle_tarxeta_equipo({"funcions": "", "ropo": ""}) == ""


def test_detalle_tarxeta_contacto_completo() -> None:
    """Papeis e teléfono sepáranse con ' · '."""
    fila = {"papeis": "Clientes, Provedores", "telefono": "600123456"}
    assert detalle_tarxeta_contacto(fila) == "Clientes, Provedores · 600123456"


def test_detalle_tarxeta_contacto_sen_telefono() -> None:
    """Se non ten teléfono, saen só as categorías sen separador."""
    fila = {"papeis": "Clientes", "telefono": ""}
    assert detalle_tarxeta_contacto(fila) == "Clientes"


def test_detalle_tarxeta_contacto_so_telefono() -> None:
    """Se non ten categorías, sae só o teléfono."""
    fila = {"papeis": "", "telefono": "600123456"}
    assert detalle_tarxeta_contacto(fila) == "600123456"


def test_detalle_tarxeta_contacto_baleiro() -> None:
    """Se non hai categorías nin teléfono, devolve cadea baleira."""
    assert detalle_tarxeta_contacto({}) == ""
    assert detalle_tarxeta_contacto({"papeis": "", "telefono": ""}) == ""
