"""Coidado e saúde dos animais: o que pide o libro de rexistro gandeiro e o rexistro de
medicamentos, o tempo de espera e que os grupos con rexistros non se borren."""

from datetime import date

import pytest

from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal, eliminar_animal
from horta.services.coidados_animais import (
    DatosCoidado,
    actualizar_coidado,
    crear_coidado,
    dar_de_baixa_coidado,
    en_tempo_espera,
    fin_tempo_espera,
    listar_coidados,
)
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.movementos_animais import DatosMovemento, crear_movemento
from horta.services.persoas import crear_contacto
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 28)


def _escenario(session, nome="Horta"):
    ana = session.query(Usuario).filter_by(email="ana@example.com").one_or_none()
    if ana is None:
        ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
        session.add(ana)
        session.commit()
    horta = crear_horta(session, ana, nome)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    galinas = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=12)
    return ana, horta, persoa, galinas


def _medicamento(galinas, persoa, **campos):
    datos = {"animal_id": galinas.id, "data_inicio": date(2026, 10, 20), "tipo": "medicamento",
             "persoa_id": persoa.id, "medicamento": "Oxitetraciclina", "tempo_espera_dias": 7,
             "duracion_dias": 5, "num_animais": 3, "receita": "R-123"}
    datos.update(campos)
    return DatosCoidado(**datos)


def test_apuntar_un_coidado_diario(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Limpar o galiñeiro", horas=1.5), hoxe=HOXE)
    assert (co.horta_id, co.data_fin, co.creado_por) == (horta.id, HOXE, ana.id)
    with pytest.raises(OperacionNonPermitidaError, match="Describe"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id),
            hoxe=HOXE)


def test_quen_o_fixo_e_obrigatorio(session):
    ana, _, _, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="quen"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=None,
            descricion="Dar de comer"), hoxe=HOXE)


def test_o_medicamento_pide_o_tempo_de_espera_aínda_que_sexa_cero(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="tempo de espera"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=None),
                      hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="medicamento"):
        crear_coidado(session, ana, _medicamento(galinas, persoa, medicamento=None), hoxe=HOXE)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa, tempo_espera_dias=0),
                       hoxe=HOXE)
    assert co.tempo_espera_dias == 0


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, horta, persoa, galinas = _escenario(session)
    ads = crear_contacto(session, ana, horta.id, "Veterinaria da ADS", None)
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id,
        visitante_id=ads.id, descricion="Revisión", matricula="1234ABC",
        medicamento="Non vai", num_animais=2), hoxe=HOXE)
    assert (co.visitante_id, co.matricula, co.produto_id, co.num_animais) == (
        ads.id, "1234ABC", None, None)
    with pytest.raises(OperacionNonPermitidaError, match="quen veu"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="visita", persoa_id=persoa.id),
            hoxe=HOXE)


def test_os_animais_afectados_non_poden_ser_mais_ca_o_grupo(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="12 animais"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="enfermidade", persoa_id=persoa.id,
            descricion="Tosen", num_animais=13), hoxe=HOXE)


def test_o_grupo_ten_que_ser_da_explotacion_e_estar_de_alta(session):
    ana, horta, persoa, galinas = _escenario(session)
    _, _, _, alleas = _escenario(session, "Outra")
    co = crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        actualizar_coidado(session, ana, co, DatosCoidado(
            animal_id=alleas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)
    crear_movemento(session, ana, DatosMovemento(
        animal_id=galinas.id, data=date(2026, 10, 1), tipo="saida", cantidade=12,
        persoa_id=persoa.id), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_coidado(session, ana, DatosCoidado(
            animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
            descricion="Auga"), hoxe=HOXE)


def test_tempo_de_espera(session):
    ana, horta, persoa, galinas = _escenario(session)
    co = crear_coidado(session, ana, _medicamento(galinas, persoa), hoxe=HOXE)
    # 5 días desde o 20 (última o 24) + 7 días de espera
    assert fin_tempo_espera(co) == date(2026, 10, 31)
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {galinas.id: date(2026, 10, 31)}
    assert en_tempo_espera(session, ana, horta.id, hoxe=date(2026, 11, 1)) == {}
    dar_de_baixa_coidado(session, ana, co)
    assert listar_coidados(session, ana, horta.id) == []
    assert en_tempo_espera(session, ana, horta.id, hoxe=HOXE) == {}


def test_un_grupo_con_coidados_non_se_borra(session):
    ana, horta, persoa, galinas = _escenario(session)
    coellos = crear_animal(session, ana, horta.id, "Coellos", date(2026, 1, 1))
    tarefa = crear_tarefa(session, ana, horta.id, "Vacinar", animal_id=coellos.id)
    eliminar_animal(session, ana, coellos)
    assert tarefa.animal_id is None
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=HOXE, tipo="coidado", persoa_id=persoa.id,
        descricion="Auga"), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="debe conservarse"):
        eliminar_animal(session, ana, galinas)
    with pytest.raises(OperacionNonPermitidaError, match="coidados de animais"):
        eliminar_horta(session, ana, horta)


def test_diario_e_tarefa_de_coidado(session):
    ana, horta, persoa, galinas = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Desparasitar", tipo="coidado_animal",
                          animal_id=galinas.id)
    assert listar_traballos(session, ana, horta.id, hoxe=HOXE)[0].onde == "Galiñas"
    co = crear_coidado(session, ana, _medicamento(galinas, persoa), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, co)
    assert (tarefa.estado, tarefa.data_feita) == ("feito", date(2026, 10, 20))
    traballos = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert [(t.tipo, t.que, t.persoas) for t in traballos] == [
        ("coidado_animal", "Medicamento — Oxitetraciclina", (persoa.id,))]


def test_a_tarefa_so_admite_animais_da_explotacion(session):
    ana, horta, _, _ = _escenario(session)
    _, _, _, alleas = _escenario(session, "Outra")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta explotación"):
        crear_tarefa(session, ana, horta.id, "Vacinar", animal_id=alleas.id)
