"""Todo traballo o fai unha persoa: apuntalo obriga a dicir quen; as horas son opcionais."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.abonados import DatosAbonado, crear_abonado
from horta.services.analises import DatosAnalise, crear_analise
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.diario import listar_traballos, sen_quen, ultima_persoa
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import DatosFertilizante, crear_fertilizante
from horta.services.hortas import crear_horta
from horta.services.labores import DatosLabor, crear_labor
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tratamentos_instalacion import (
    DatosTratamentoInstalacion,
    crear_tratamento_instalacion,
)

HOXE = date(2026, 10, 27)


def _escenario(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("material_fertilizante", "13"), ("tipo_labor", "7"),
                             ("material_analizado", "3")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=codigo,
                                  version_id=v.id))
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x", rol=RolGlobal.USUARIO,
                  activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    ana_persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    parcela = crear_parcela(session, ana, horta.id, "Horta")
    return ana, horta, ana_persoa, crear_cultivo(session, ana, parcela.id, "Tomate")


def _apuntar(session, ana, horta, cultivo, tipo, persoa_id, horas=None):
    if tipo == "rega":
        return crear_rega(session, ana, DatosRega(
            cultivo_id=cultivo.id, data_inicio=HOXE, persoa_id=persoa_id, horas=horas),
            hoxe=HOXE)
    if tipo == "labor":
        return crear_labor(session, ana, DatosLabor(
            cultivo_id=cultivo.id, data_inicio=HOXE, tipo_labor="7", persoa_id=persoa_id,
            horas=horas), hoxe=HOXE)
    if tipo == "colleita":
        return crear_colleita(session, ana, DatosColleita(
            cultivo_id=cultivo.id, data=HOXE, cantidade=5, unidade="kg", lote="",
            persoa_id=persoa_id, horas=horas), hoxe=HOXE)
    if tipo == "analise":
        return crear_analise(session, ana, horta.id, DatosAnalise(
            material_analizado="3", data_mostraxe=HOXE, persoa_id=persoa_id, horas=horas),
            hoxe=HOXE)
    if tipo == "tratamento_instalacion":
        return crear_tratamento_instalacion(session, ana, horta.id, DatosTratamentoInstalacion(
            tipo="local", data=HOXE, obxecto="Almacén", materia_activa="Cal",
            persoa_id=persoa_id, horas=horas), hoxe=HOXE)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    return crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        aplicador_persoa_id=persoa_id, horas=horas), hoxe=HOXE)


TIPOS = ["rega", "labor", "colleita", "analise", "tratamento_instalacion", "abonado"]


@pytest.mark.parametrize("tipo", TIPOS)
def test_sen_quen_non_se_garda(session, tipo):
    ana, horta, _, cultivo = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="Indica quen o fixo"):
        _apuntar(session, ana, horta, cultivo, tipo, None)


@pytest.mark.parametrize("tipo", TIPOS)
def test_garda_quen_e_as_horas(session, tipo):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    rexistro = _apuntar(session, ana, horta, cultivo, tipo, ana_persoa.id, horas=1.5)
    persoa_id = rexistro.aplicador_persoa_id if tipo == "abonado" else rexistro.persoa_id
    assert persoa_id == ana_persoa.id and rexistro.horas == 1.5


def test_as_horas_son_opcionais_pero_positivas(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    assert _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id).horas is None
    with pytest.raises(OperacionNonPermitidaError, match="horas"):
        _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id, horas=0)


def test_a_persoa_ten_que_ser_da_explotacion(session):
    ana, horta, _, cultivo = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    de_fora = session.query(Persoa).filter_by(horta_id=outra.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        _apuntar(session, ana, horta, cultivo, "rega", de_fora.id)


def test_abonado_dunha_empresa_de_servizos_sen_persoa(session):
    ana, horta, _, cultivo = _escenario(session)
    esterco = crear_fertilizante(session, ana, horta.id, DatosFertilizante(
        nome="Compost", material="13"))
    abonado = crear_abonado(session, ana, DatosAbonado(
        cultivo_id=cultivo.id, data_inicio=HOXE, fertilizante_id=esterco.id,
        empresa_servizos_regfer="ES1234"), hoxe=HOXE)
    assert abonado.aplicador_persoa_id is None


def test_sementeira_garda_quen_e_as_horas(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    actualizar_cultivo(session, ana, cultivo, sementeira_persoa_id=ana_persoa.id,
                       sementeira_horas=3)
    assert cultivo.sementeira_persoa_id == ana_persoa.id and cultivo.sementeira_horas == 3
    outra = crear_horta(session, ana, "Outra")
    de_fora = session.query(Persoa).filter_by(horta_id=outra.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        actualizar_cultivo(session, ana, cultivo, sementeira_persoa_id=de_fora.id)


def test_o_diario_sabe_quen_o_fixo(session):
    ana, horta, ana_persoa, cultivo = _escenario(session)
    assert ultima_persoa(session, ana, horta.id) is None
    rega = _apuntar(session, ana, horta, cultivo, "rega", ana_persoa.id)
    [traballo] = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert traballo.persoas == (ana_persoa.id,) and not traballo.sen_quen
    assert ultima_persoa(session, ana, horta.id) == ana_persoa.id
    # Os rexistros de antes, sen persoa, avísanse
    rega.persoa_id = None
    session.commit()
    assert sen_quen(session, ana, horta.id) == {"rega": 1}
