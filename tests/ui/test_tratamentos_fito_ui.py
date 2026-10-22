import pytest

from horta.services.errors import OperacionNonPermitidaError
from horta.ui.pages.tratamentos_fito import _obrigatoria


def test_data_obrigatoria():
    with pytest.raises(OperacionNonPermitidaError, match="Indica as datas"):
        _obrigatoria(None)
