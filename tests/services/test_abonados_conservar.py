from datetime import date

import pytest

from horta.models.abonado import Abonado, AbonadoCultivo
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    session.add(Abonado(horta_id=horta.id, data_inicio=date(2026, 4, 1),
                        data_fin=date(2026, 4, 1), tipo_fertilizacion="1",
                        metodo="1",
                        leiras=[AbonadoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1)]))
    session.commit()
    return ana, horta, parcela, cultivo


def test_non_se_borra_un_cultivo_con_abonados(session):
    ana, _, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_cultivo(session, ana, cultivo)


def test_non_se_borra_unha_parcela_con_abonados(session):
    ana, _, parcela, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="abonados"):
        eliminar_parcela(session, ana, parcela)
