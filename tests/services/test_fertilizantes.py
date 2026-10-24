import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.fertilizante import FertilizanteSiex
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import (
    DatosFertilizante,
    crear_fertilizante,
    datos_desde_siex,
    dose_kg_ha,
    listar_fertilizantes,
    nutrientes_kg_ha,
)
from horta.services.hortas import crear_horta


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for codigo in ("5", "14"):
        session.add(CatalogoValor(catalogo="material_fertilizante", codigo=codigo,
                                  descricion="m", version_id=v.id))
    session.add(FertilizanteSiex(codigo=2, material="14", nome="NITRATO (34,5-00-00)",
                                 n_pct=34.5, version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_crear_desde_o_catalogo_oficial(session):
    ana, horta = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, datos_desde_siex(session, 2))
    assert abono.material == "14" and abono.n_pct == 34.5
    assert [f.nome for f in listar_fertilizantes(session, ana, horta.id)] == [
        "NITRATO (34,5-00-00)"]


def test_esterco_pide_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="de onde veñen"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="Esterco", material="5"))
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Esterco", material="5", provedor_nome="Casa", n_pct=0.6))
    assert abono.provedor_nome == "Casa"


def test_so_un_identificador_do_provedor(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="só un"):
        crear_fertilizante(session, ana, horta.id, DatosFertilizante(
            nome="E", material="5", provedor_nome="X", provedor_nif="1", provedor_rega="2"))


def test_nome_repetido(session):
    ana, horta = _escenario(session)
    crear_fertilizante(session, ana, horta.id, DatosFertilizante(nome="Nitrato", material="14"))
    with pytest.raises(OperacionNonPermitidaError, match="Xa tes"):
        crear_fertilizante(session, ana, horta.id,
                           DatosFertilizante(nome=" Nitrato ", material="14"))


@pytest.mark.parametrize(("dose", "unidade", "densidade", "esperado"), [
    (200, "17", None, 200),      # kg/ha
    (2, "29", None, 2000),       # t/ha
    (50, "80", None, 500),       # g/m²
    (100, "18", 1.4, 140),       # L/ha con densidade
    (100, "18", None, None),     # L/ha sen densidade: non se sabe
    (3, "2", None, None),        # ha non é unha dose
])
def test_dose_kg_ha(dose, unidade, densidade, esperado):
    assert dose_kg_ha(dose, unidade, densidade) == esperado


def test_nutrientes_dunha_dose(session):
    ana, horta = _escenario(session)
    abono = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="NPK", material="14", n_pct=15, p2o5_pct=15, k2o_pct=15))
    assert nutrientes_kg_ha(abono, 200, "17") == (30.0, 30.0, 30.0)
