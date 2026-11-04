"""Números en texto con coma decimal (Y10)."""

from horta.services.formato import num_texto


def test_coma_decimal():
    assert num_texto(0.3) == "0,3"


def test_sen_decimais_se_e_enteiro():
    assert num_texto(2.0) == "2"
    assert num_texto(1500) == "1500"


def test_como_moito_tres_decimais():
    assert num_texto(0.12345) == "0,123"
