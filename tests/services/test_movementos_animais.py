"""Entradas e saídas de animais: o que pide o libro de rexistro gandeiro e que a cantidade
de cada grupo saia dos seus movementos."""

from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import actualizar_animal, crear_animal, eliminar_animal
from horta.services.coidados_animais import DatosCoidado, crear_coidado
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.movementos_animais import (
    DatosMovemento,
    actualizar_movemento,
    aviso_tempo_espera,
    crear_movemento,
    dar_de_baixa_movemento,
    listar_movementos,
)
from horta.services.persoas import crear_contacto
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 28)
ALTA = date(2026, 3, 1)


def _escenario(session, nome="Horta"):
    ana = session.query(Usuario).filter_by(email="ana@example.com").one_or_none()
    if ana is None:
        ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                      rol=RolGlobal.USUARIO, activo=True)
        session.add(ana)
        session.commit()
    horta = crear_horta(session, ana, nome)
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    galinas = crear_animal(session, ana, horta.id, "Galiñas", ALTA, cantidade=10)
    return ana, horta, persoa, galinas


def _mov(galinas, persoa, tipo, cantidade, dia=date(2026, 9, 1), **campos):
    return DatosMovemento(animal_id=galinas.id, data=dia, tipo=tipo, cantidade=cantidade,
                          persoa_id=persoa.id, **campos)


def test_a_cantidade_sae_dos_movementos(session):
    ana, horta, persoa, galinas = _escenario(session)
    assert listar_movementos(session, ana, horta.id) == []  # o inicial non se lista
    crear_movemento(session, ana, _mov(galinas, persoa, "nacemento", 4), hoxe=HOXE)
    xan = crear_contacto(session, ana, horta.id, "Xan, Lalín", "explotacion",
                         rega="ES360000000001")
    entrada = crear_movemento(session, ana, _mov(galinas, persoa, "entrada", 6,
                                                 outra_parte_id=xan.id), hoxe=HOXE)
    assert entrada.outra_parte_id == xan.id
    saida = crear_movemento(session, ana, _mov(galinas, persoa, "saida", 5), hoxe=HOXE)
    crear_movemento(session, ana, _mov(galinas, persoa, "morte", 1, causa="Raposo"),
                    hoxe=HOXE)
    assert galinas.cantidade == 14
    dar_de_baixa_movemento(session, ana, saida)
    assert galinas.cantidade == 19


def test_non_poden_sair_mais_dos_que_hai_ningun_dia(session):
    ana, _, persoa, galinas = _escenario(session)
    crear_movemento(session, ana, _mov(galinas, persoa, "entrada", 5, dia=date(2026, 9, 10)),
                    hoxe=HOXE)
    # O 1/9 só había 10, aínda que despois entrasen 5
    with pytest.raises(OperacionNonPermitidaError, match="máis animais dos que había"):
        crear_movemento(session, ana, _mov(galinas, persoa, "saida", 12), hoxe=HOXE)
    assert galinas.cantidade == 15
    entrada = listar_movementos(session, ana, galinas.horta_id)[0]
    crear_movemento(session, ana, _mov(galinas, persoa, "saida", 12, dia=date(2026, 9, 20)),
                    hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="máis animais"):
        dar_de_baixa_movemento(session, ana, entrada)


def test_a_cero_o_grupo_queda_de_baixa_e_volve_ao_entrar(session):
    ana, _, persoa, galinas = _escenario(session)
    crear_movemento(session, ana, _mov(galinas, persoa, "saida", 10), hoxe=HOXE)
    assert (galinas.cantidade, galinas.estado, galinas.data_baixa) == (
        0, "baixa", date(2026, 9, 1))
    crear_movemento(session, ana, _mov(galinas, persoa, "entrada", 3, dia=date(2026, 10, 1)),
                    hoxe=HOXE)
    assert (galinas.cantidade, galinas.estado, galinas.data_baixa) == (3, "activo", None)


def test_cada_tipo_garda_so_os_seus_datos(session):
    ana, horta, persoa, galinas = _escenario(session)
    xan = crear_contacto(session, ana, horta.id, "Xan", "explotacion")
    mov = crear_movemento(session, ana, _mov(
        galinas, persoa, "nacemento", 2, outra_parte_id=xan.id, causa="Non vai",
        identificacion="Anelas 1 e 2"), hoxe=HOXE)
    assert (mov.outra_parte_id, mov.causa, mov.identificacion) == (
        None, None, "Anelas 1 e 2")
    actualizar_movemento(session, ana, mov, _mov(galinas, persoa, "morte", 2, causa="Frío"),
                         hoxe=HOXE)
    assert (mov.tipo, mov.causa, galinas.cantidade) == ("morte", "Frío", 8)


def test_validacions(session):
    ana, _, persoa, galinas = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="quen"):
        crear_movemento(session, ana, DatosMovemento(galinas.id, date(2026, 9, 1), "saida", 1,
                                                     None), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="polo menos 1"):
        crear_movemento(session, ana, _mov(galinas, persoa, "saida", 0), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="alta"):
        crear_movemento(session, ana, _mov(galinas, persoa, "saida", 1, dia=date(2026, 2, 1)),
                        hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="futura"):
        crear_movemento(session, ana, _mov(galinas, persoa, "saida", 1, dia=date(2026, 11, 1)),
                        hoxe=HOXE)


def test_data_de_alta_e_especie(session):
    ana, horta, persoa, galinas = _escenario(session)
    version = CatalogoVersion(catalogo="especie_animal", nome_ficheiro="x", sha256="e" * 64,
                              filas=1)
    session.add(version)
    session.flush()
    session.add(CatalogoValor(catalogo="especie_animal", codigo="06", descricion="Gallinas",
                              version_id=version.id))
    session.commit()
    actualizar_animal(session, ana, galinas, data_alta=date(2026, 1, 15), especie_codigo="06")
    assert (galinas.data_alta, galinas.especie_codigo, galinas.cantidade) == (
        date(2026, 1, 15), "06", 10)
    with pytest.raises(OperacionNonPermitidaError, match="lista"):
        crear_animal(session, ana, horta.id, "Peixes", ALTA, especie_codigo="29")
    crear_movemento(session, ana, _mov(galinas, persoa, "saida", 1, dia=date(2026, 2, 1)),
                    hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="non pode ser posterior"):
        actualizar_animal(session, ana, galinas, data_alta=date(2026, 3, 1))


def test_non_se_borra_un_grupo_con_movementos(session):
    ana, horta, persoa, galinas = _escenario(session)
    coellos = crear_animal(session, ana, horta.id, "Coellos", ALTA, cantidade=2)
    eliminar_animal(session, ana, coellos)  # só o inicial: bórrase
    crear_movemento(session, ana, _mov(galinas, persoa, "saida", 1), hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="debe conservarse"):
        eliminar_animal(session, ana, galinas)
    with pytest.raises(OperacionNonPermitidaError, match="entradas e saídas"):
        eliminar_horta(session, ana, horta)


def test_borrar_a_explotacion_sen_movementos_borra_os_iniciais(session):
    ana, horta, _, _ = _escenario(session)
    eliminar_horta(session, ana, horta)


def test_aviso_de_tempo_de_espera(session):
    ana, horta, persoa, galinas = _escenario(session)
    crear_coidado(session, ana, DatosCoidado(
        animal_id=galinas.id, data_inicio=date(2026, 10, 20), tipo="medicamento",
        persoa_id=persoa.id, medicamento="Oxitetraciclina", tempo_espera_dias=7), hoxe=HOXE)
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, "saida", date(2026, 10, 25)
                              ) == "Este grupo está en tempo de espera ata o 27/10/2026"
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, "saida", HOXE) is None
    assert aviso_tempo_espera(session, ana, horta.id, galinas.id, "nacemento",
                              date(2026, 10, 25)) is None


def test_diario_e_tarefa(session):
    ana, horta, persoa, galinas = _escenario(session)
    tarefa = crear_tarefa(session, ana, horta.id, "Levar á feira", tipo="movemento_animal",
                          animal_id=galinas.id)
    mov = crear_movemento(session, ana, _mov(galinas, persoa, "saida", 4), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, mov)
    assert (tarefa.estado, tarefa.data_feita) == ("feito", date(2026, 9, 1))
    assert [(t.tipo, t.que, t.onde) for t in listar_traballos(session, ana, horta.id,
                                                               hoxe=HOXE)] == [
        ("movemento_animal", "Saída: 4", "Galiñas")]
