from datetime import date, time

import pytest

from horta.services.errors import OperacionNonPermitidaError
from horta.ui.pages.tratamentos_fito import _data, _hora


def test_data_valida_e_invalida():
    assert _data(" 2026-05-01 ") == date(2026, 5, 1)
    with pytest.raises(OperacionNonPermitidaError, match="Data non válida"):
        _data("32/13/2026")


def test_hora_opcional_e_invalida():
    assert _hora("") is None
    assert _hora("09:30") == time(9, 30)
    with pytest.raises(OperacionNonPermitidaError, match="Hora non válida"):
        _hora("9h")
