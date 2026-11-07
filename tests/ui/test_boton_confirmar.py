"""Texto do botón de confirmar."""

from horta.ui.boton_confirmar import boton_para


def test_dar_de_baixa():
    assert boton_para("Dar de baixa esta rega? Non se borra.") == ("Dar de baixa", "archive")


def test_eliminar():
    assert boton_para("Eliminar esta parcela e os seus cultivos?") == ("Eliminar", "delete")
