import pytest

from horta.ui.numeros import parsear_decimal


@pytest.mark.parametrize("entrada,esperado", [
    ("1,5", 1.5), ("1.5", 1.5), (" 2 ", 2.0), ("", None), (None, None), (3, 3.0),
])
def test_parsear_decimal(entrada, esperado):
    assert parsear_decimal(entrada) == esperado


def test_parsear_decimal_invalido():
    with pytest.raises(ValueError, match="non é un número"):
        parsear_decimal("abc")


def test_parsear_data_e_hora():
    from datetime import date, time

    from horta.ui.numeros import parsear_data, parsear_hora

    assert parsear_data("2026-05-01") == date(2026, 5, 1)
    assert parsear_data("") is None
    assert parsear_hora("") is None and parsear_hora("09:30") == time(9, 30)
    with pytest.raises(ValueError, match="Data non válida"):
        parsear_data("32/13/2026")
