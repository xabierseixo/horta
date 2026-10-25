from datetime import date

import pytest

from horta.models.rega import Rega
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.parcelas import crear_parcela, eliminar_parcela


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1")
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate")
    session.add(Rega(horta_id=horta.id, cultivo_id=cultivo.id, data_inicio=date(2026, 7, 1),
                     data_fin=date(2026, 7, 1), superficie_ha=0.01, sistema_rega="6",
                     cantidade=300, unidade="4"))
    session.commit()
    return ana, horta, parcela, cultivo


def test_non_se_borra_un_cultivo_con_regas(session):
    ana, _, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="regas"):
        eliminar_cultivo(session, ana, cultivo)


def test_non_se_borra_unha_parcela_con_regas(session):
    ana, _, parcela, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="regas"):
        eliminar_parcela(session, ana, parcela)


def test_non_se_borra_unha_explotacion_con_regas(session):
    ana, horta, _, _ = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="regas"):
        eliminar_horta(session, ana, horta)
