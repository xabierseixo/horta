"""Probas para as tarxetas de grupos de animais no móbil (detalle_tarxeta_animal)."""

from __future__ import annotations

from horta.ui.pages.animais import detalle_tarxeta_animal


def test_detalle_tarxeta_animal_completo() -> None:
    """Grupo con especie, cantidade, tempo de espera e pasto."""
    fila = {
        "especie": "Galiñas",
        "cantidade": 12,
        "espera": "En tempo de espera ata 20/05/2026",
        "pasto": "No pasto: Leira grande desde o 12/04",
    }
    assert detalle_tarxeta_animal(fila) == (
        "Galiñas · 12 animais · En tempo de espera ata 20/05/2026 · "
        "No pasto: Leira grande desde o 12/04"
    )


def test_detalle_tarxeta_animal_un_animal() -> None:
    """Grupo cun só animal usa o singular «animal»."""
    fila = {
        "especie": "Vacas",
        "cantidade": 1,
        "espera": "",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == "Vacas · 1 animal"


def test_detalle_tarxeta_animal_sen_espera_nin_pasto() -> None:
    """Grupo con especie e cantidade sen espera nin pasto."""
    fila = {
        "especie": "Porcos",
        "cantidade": 5,
        "espera": "",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == "Porcos · 5 animais"


def test_detalle_tarxeta_animal_so_espera() -> None:
    """Grupo con tempo de espera pero sen pasto."""
    fila = {
        "especie": "Ovellas",
        "cantidade": 10,
        "espera": "En tempo de espera ata 10/11/2026",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == "Ovellas · 10 animais · En tempo de espera ata 10/11/2026"


def test_detalle_tarxeta_animal_so_pasto() -> None:
    """Grupo no pasto pero sen tempo de espera."""
    fila = {
        "especie": "Cabras",
        "cantidade": 4,
        "espera": "",
        "pasto": "No pasto: Devesa desde o 01/05",
    }
    assert detalle_tarxeta_animal(fila) == "Cabras · 4 animais · No pasto: Devesa desde o 01/05"


def test_detalle_tarxeta_animal_sen_especie() -> None:
    """Se non ten especie, mostra a cantidade sen texto previo."""
    fila = {
        "especie": "",
        "cantidade": 3,
        "espera": "",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == "3 animais"


def test_detalle_tarxeta_animal_cero_animais() -> None:
    """Se a cantidade é cero, móstrase como «0 animais»."""
    fila = {
        "especie": "Coellos",
        "cantidade": 0,
        "espera": "",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == "Coellos · 0 animais"


def test_detalle_tarxeta_animal_baleiro() -> None:
    """Se non ten ningún dato, devolve cadea baleira."""
    fila = {
        "especie": "",
        "cantidade": None,
        "espera": "",
        "pasto": "",
    }
    assert detalle_tarxeta_animal(fila) == ""
