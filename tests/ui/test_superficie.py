import pytest

from horta.ui.superficie import a_hectareas, desde_hectareas, formatar_superficie


def test_m2_a_hectareas():
    assert a_hectareas(250, "m²") == 0.025


def test_ha_queda_igual():
    assert a_hectareas(1.5, "ha") == 1.5


def test_hectareas_a_m2():
    assert desde_hectareas(0.025, "m²") == 250


@pytest.mark.parametrize("funcion", [a_hectareas, desde_hectareas])
def test_baleiro_queda_baleiro(funcion):
    assert funcion(None, "m²") is None


def test_formatar_superficie():
    assert formatar_superficie(0.025) == "250 m²"
    assert formatar_superficie(1.5) == "1,50 ha"
    assert formatar_superficie(None) == ""
