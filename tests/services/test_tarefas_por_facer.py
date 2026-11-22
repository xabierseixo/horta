"""As tarefas son traballos por facer: levan o tipo e, ao facelas, quedan ligadas ao
rexistro dese tipo (non hai dúas listas). Sen tipo, pídese quen a fixo."""

from datetime import date

import pytest

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import crear_cultivo
from horta.services.diario import listar_traballos, sen_quen
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega
from horta.services.tarefas import (
    actualizar_tarefa,
    crear_tarefa,
    facer_tarefa,
    marcar_feita,
    marcar_pendente,
)

HOXE = date(2026, 10, 27)


def _escenario(session, nome="Horta"):
    ana = session.query(Usuario).filter_by(email="ana@example.com").one_or_none()
    if ana is None:
        ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
        session.add(ana)
        session.commit()
    horta = crear_horta(session, ana, nome)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    parcela = crear_parcela(session, ana, horta.id, "Horta de abaixo")
    return ana, horta, persoa, crear_cultivo(session, ana, parcela.id, "Tomate")


def _rega(session, ana, cultivo, persoa):
    return crear_rega(session, ana, DatosRega(cultivo_id=cultivo.id, data_inicio=HOXE,
                                              persoa_id=persoa.id), hoxe=HOXE)


def test_a_tarefa_leva_o_tipo_e_quen_a_vai_facer(session):
    ana, horta, persoa, cultivo = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Regar os tomates", tipo="rega",
                          cultivo_id=cultivo.id, persoa_id=persoa.id)
    assert (tarefa.tipo, tarefa.persoa_id) == ("rega", persoa.id)
    with pytest.raises(OperacionNonPermitidaError, match="tipo"):
        crear_tarefa(session, ana, horta.id, "Sementar", tipo="sementeira")


def test_quen_a_vai_facer_ten_que_ser_da_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    _, _, de_fora, _ = _escenario(session, "Outra")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_tarefa(session, ana, horta.id, "Regar", persoa_id=de_fora.id)


def test_facela_ligaa_ao_traballo_e_o_diario_non_a_repite(session):
    ana, horta, persoa, cultivo = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Regar os tomates", tipo="rega",
                          cultivo_id=cultivo.id)
    rega = _rega(session, ana, cultivo, persoa)
    facer_tarefa(session, ana, tarefa, rega)
    assert (tarefa.estado, tarefa.data_feita, tarefa.traballo_id) == ("feito", HOXE, rega.id)
    assert [t.tipo for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)] == ["rega"]


def test_o_traballo_ten_que_ser_do_tipo_e_da_explotacion(session):
    ana, horta, persoa, cultivo = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Colleitar", tipo="colleita")
    with pytest.raises(OperacionNonPermitidaError, match="tipo"):
        facer_tarefa(session, ana, tarefa, _rega(session, ana, cultivo, persoa))
    _, _, persoa2, cultivo2 = _escenario(session, "Outra")
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo2.id, data=HOXE, cantidade=5, unidade="kg", lote="",
        persoa_id=persoa2.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="explotación"):
        facer_tarefa(session, ana, tarefa, colleita)


def test_unha_tarefa_con_tipo_apuntase_no_seu_formulario(session):
    ana, horta, persoa, _ = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Regar", tipo="rega")
    with pytest.raises(OperacionNonPermitidaError, match="formulario"):
        marcar_feita(session, ana, tarefa, persoa.id)


def test_sen_tipo_pide_quen_a_fixo_e_garda_as_horas(session):
    ana, horta, persoa, _ = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Limpar o galiñeiro")
    with pytest.raises(OperacionNonPermitidaError, match="Indica quen o fixo"):
        marcar_feita(session, ana, tarefa, None)
    marcar_feita(session, ana, tarefa, persoa.id, data=HOXE, horas=2)
    assert (tarefa.estado, tarefa.persoa_id, tarefa.horas, tarefa.data_feita) == (
        "feito", persoa.id, 2, HOXE)
    (traballo,) = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert traballo.persoas == (persoa.id,) and not traballo.sen_quen


def test_as_feitas_de_antes_sen_quen_avisanse(session):
    ana, horta, persoa, _ = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Limpar o galiñeiro")
    marcar_feita(session, ana, tarefa, persoa.id, data=HOXE)
    tarefa.persoa_id = None
    session.commit()
    assert sen_quen(session, ana, horta.id) == {"tarefa": 1}


def test_unha_tarefa_xa_apuntada_non_volve_a_por_facer_nin_cambia_de_tipo(session):
    ana, horta, persoa, cultivo = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Regar", tipo="rega")
    facer_tarefa(session, ana, tarefa, _rega(session, ana, cultivo, persoa))
    with pytest.raises(OperacionNonPermitidaError, match="edita ese traballo"):
        marcar_pendente(session, ana, tarefa)
    with pytest.raises(OperacionNonPermitidaError, match="tipo"):
        actualizar_tarefa(session, ana, tarefa, tipo="labor")
