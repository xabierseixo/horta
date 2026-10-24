from datetime import date

import pytest

from horta.models.abonado import Abonado, Fertilizante
from horta.models.horta import Horta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    session.add(Fertilizante(horta_id=horta.id, nome="Esterco", material="5"))
    session.commit()
    return ana, horta


def test_non_se_borra_unha_explotacion_con_abonados(session):
    ana, horta = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    session.add(Abonado(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), superficie_ha=0.1, tipo_fertilizacion="1",
                        metodo="1"))
    session.commit()
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_horta(session, ana, horta)


def test_borrar_explotacion_sen_abonados_borra_os_seus_abonos(session):
    ana, horta = _escenario(session)
    eliminar_horta(session, ana, horta)
    assert session.get(Horta, horta.id) is None
    assert session.query(Fertilizante).count() == 0
