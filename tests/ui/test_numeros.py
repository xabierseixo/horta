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
