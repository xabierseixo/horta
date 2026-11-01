from datetime import date

import pytest

from horta.models.catalogo import CatalogoVersion, CultivoSiex
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo, ten_rexistros
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela

HOXE = date(2026, 10, 1)


def _escenario(session, con_colleita=True):
    v = CatalogoVersion(catalogo="cultivo", nome_ficheiro="x", sha256="d" * 64, filas=2)
    session.add(v)
    session.flush()
    session.add_all([CultivoSiex(codigo=117, nome_oficial="TOMATE", version_id=v.id),
                     CultivoSiex(codigo=118, nome_oficial="PIMIENTO", version_id=v.id)])
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    parcela = crear_parcela(session, ana, horta.id, "Leira", superficie=1.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Tomate", cultivo_siex_codigo=117,
                            superficie_ha=0.5, data_inicio=date(2026, 4, 1))
    if con_colleita:
        crear_colleita(session, ana, DatosColleita(
            cultivo_id=cultivo.id, data=date(2026, 8, 1), data_fin=date(2026, 8, 10),
            cantidade=100.0, unidade="kg", lote="L-1", persoa_id=quen.id,
            superficie_ha=0.4), hoxe=HOXE)
    return ana, cultivo


def test_con_traballos_non_se_cambia_o_cultivo(session):
    ana, cultivo = _escenario(session)
    assert ten_rexistros(session, cultivo.id)
    with pytest.raises(OperacionNonPermitidaError, match="non se pode cambiar a outro cultivo"):
        actualizar_cultivo(session, ana, cultivo, cultivo_siex_codigo=118)


def test_con_traballos_si_se_cambia_a_variedade(session):
    ana, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, cultivo_siex_codigo=117, variedade="Marmande")
    assert cultivo.variedade == "Marmande"


def test_sen_traballos_si_se_cambia_o_cultivo(session):
    ana, cultivo = _escenario(session, con_colleita=False)
    actualizar_cultivo(session, ana, cultivo, cultivo_siex_codigo=118)
    assert cultivo.cultivo_siex_codigo == 118


def test_inicio_despois_da_colleita(session):
    ana, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="Hai colleitas desde o 01/08/2026"):
        actualizar_cultivo(session, ana, cultivo, data_inicio=date(2026, 8, 2))


def test_fin_antes_da_ultima_colleita(session):
    ana, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="A última colleita é do 10/08/2026"):
        actualizar_cultivo(session, ana, cultivo, data_fin=date(2026, 8, 5))


def test_superficie_menor_ca_colleita(session):
    ana, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="foi en 0,4 ha"):
        actualizar_cultivo(session, ana, cultivo, superficie_ha=0.3)
