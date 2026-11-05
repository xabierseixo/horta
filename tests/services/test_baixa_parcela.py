"""D4: unha parcela con historial non se borra, dáse de baixa con data e causa."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela, dar_de_baixa_parcela, ten_historial

HOXE = date(2026, 10, 25)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="d" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add(CatalogoValor(catalogo="causa_baixa", codigo="2", descricion="Fin do arrendo",
                              version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    return ana, horta, crear_parcela(session, ana, horta.id, "Leira")


def test_dar_de_baixa(session):
    ana, _, parcela = _escenario(session)
    dar_de_baixa_parcela(session, ana, parcela, date(2026, 10, 1), "2", hoxe=HOXE)
    assert (parcela.data_baixa, parcela.causa_baixa, parcela.estado) == (
        date(2026, 10, 1), "2", "baixa")


def test_cun_cultivo_sen_rematar_non(session):
    ana, _, parcela = _escenario(session)
    crear_cultivo(session, ana, parcela.id, "Millo")
    with pytest.raises(OperacionNonPermitidaError, match="Remata antes"):
        dar_de_baixa_parcela(session, ana, parcela, date(2026, 10, 1), "2", hoxe=HOXE)


def test_cun_cultivo_rematado_si(session):
    ana, _, parcela = _escenario(session)
    cultivo = crear_cultivo(session, ana, parcela.id, "Millo")
    actualizar_cultivo(session, ana, cultivo, data_inicio=date(2026, 4, 1),
                       data_fin=date(2026, 9, 1))
    dar_de_baixa_parcela(session, ana, parcela, date(2026, 10, 1), "2", hoxe=HOXE)
    assert parcela.estado == "baixa"


@pytest.mark.parametrize(("dia", "causa", "mensaxe"), [
    (date(2026, 11, 1), "2", "futura"),
    (date(2026, 10, 1), None, "causa"),
])
def test_validacions(session, dia, causa, mensaxe):
    ana, _, parcela = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        dar_de_baixa_parcela(session, ana, parcela, dia, causa, hoxe=HOXE)


def test_non_se_planta_nunha_parcela_de_baixa(session):
    ana, _, parcela = _escenario(session)
    dar_de_baixa_parcela(session, ana, parcela, date(2026, 10, 1), "2", hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_cultivo(session, ana, parcela.id, "Millo")


def test_ten_historial(session):
    ana, _, parcela = _escenario(session)
    assert not ten_historial(session, parcela)
