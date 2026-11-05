"""Probas do cálculo da TIR (Tarefa 135)."""

from horta.services.plan_empresa import _tir


def test_tir_maior_ca_100():
    """Se a TIR é maior ca 100 %, dobra alto ata atopar cambio de signo."""
    tir = _tir([-100, 300, 300])
    assert tir is not None
    assert tir > 1.0
    assert tir == 2.7913


def test_tir_menor_ca_100():
    """Fluxos estándar cunha TIR do 10 % (0.1)."""
    tir = _tir([-100, 110])
    assert tir == 0.1


def test_tir_sen_cambio_de_signo():
    """Sen cambio de signo nos fluxos, non hai TIR."""
    assert _tir([100, 200]) is None
    assert _tir([-100, -200]) is None


def test_tir_maior_ca_maximo():
    """Se a TIR supera o máximo de 10 000 % (alto=100.0), devolve None."""
    assert _tir([-1, 1000]) is None
