"""Dividir, xuntar e recortar lindes."""

import pytest

from horta.services.errors import OperacionNonPermitidaError
from horta.services.xeometria import dividir, recortar, xuntar

# Un cadrado de 0,001° de lado
CADRADO = [(42.0, -8.0), (42.001, -8.0), (42.001, -7.999), (42.0, -7.999)]


def _area(puntos):
    return abs(sum(a[1] * b[0] - b[1] * a[0]
                   for a, b in zip(puntos, puntos[1:] + puntos[:1], strict=True))) / 2


def test_dividir_pola_metade():
    a, b = dividir(CADRADO, [(41.999, -7.9995), (42.002, -7.9995)])
    assert _area(a) == pytest.approx(_area(b)) == pytest.approx(_area(CADRADO) / 2)


def test_a_liña_ten_que_cruzar():
    with pytest.raises(OperacionNonPermitidaError, match="lado a lado"):
        dividir(CADRADO, [(41.999, -7.9995), (42.0005, -7.9995)])


def test_dividir_e_volver_xuntar():
    a, b = dividir(CADRADO, [(41.999, -7.9995), (42.002, -7.9995)])
    assert _area(xuntar(a, b)) == pytest.approx(_area(CADRADO), rel=1e-3)


def test_non_se_xuntan_se_non_se_tocan():
    lonxe = [(la + 0.01, lo) for la, lo in CADRADO]
    with pytest.raises(OperacionNonPermitidaError, match="se toquen"):
        xuntar(CADRADO, lonxe)


def test_recortar_polo_recinto():
    saido = [(42.0005, -8.0005), (42.0015, -8.0005), (42.0015, -7.9995), (42.0005, -7.9995)]
    dentro = recortar(saido, CADRADO)
    assert _area(dentro) == pytest.approx(_area(CADRADO) / 4)
    with pytest.raises(OperacionNonPermitidaError, match="dentro do recinto"):
        recortar([(la + 0.01, lo) for la, lo in CADRADO], CADRADO)
