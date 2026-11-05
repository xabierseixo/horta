"""G4: un coidado pasado compárase cos animais que había ese día, non cos de hoxe."""

from datetime import date

import pytest
from test_coidados_animais import _escenario, _medicamento

from horta.services.coidados_animais import crear_coidado
from horta.services.errors import OperacionNonPermitidaError
from horta.services.movementos_animais import DatosMovemento, crear_movemento

HOXE = date(2026, 10, 25)


def _morren_9(session, ana, galinas, persoa):
    crear_movemento(session, ana, DatosMovemento(
        animal_id=galinas.id, data=date(2026, 6, 1), tipo="morte", cantidade=9,
        persoa_id=persoa.id, causa="Raposo"), hoxe=HOXE)
    assert galinas.cantidade == 3


def test_coidado_de_antes_conta_os_animais_daquela(session):
    ana, _, persoa, galinas = _escenario(session)
    _morren_9(session, ana, galinas, persoa)
    coidado = crear_coidado(session, ana, _medicamento(
        galinas, persoa, data_inicio=date(2026, 3, 1), num_animais=10), hoxe=HOXE)
    assert coidado.num_animais == 10


def test_coidado_de_despois_non_pasa_dos_que_quedan(session):
    ana, _, persoa, galinas = _escenario(session)
    _morren_9(session, ana, galinas, persoa)
    with pytest.raises(OperacionNonPermitidaError, match="só tiña 3"):
        crear_coidado(session, ana, _medicamento(
            galinas, persoa, data_inicio=date(2026, 7, 1), num_animais=10), hoxe=HOXE)
