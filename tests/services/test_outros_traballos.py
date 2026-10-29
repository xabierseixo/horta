"""Outro traballo: mantemento, limpeza, arranxos…
."""

from datetime import date

import pytest

from horta.models.outro_traballo import OutroTraballo
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import crear_animal, eliminar_animal
from horta.services.diario import listar_traballos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta, eliminar_horta
from horta.services.outros_traballos import (
    DatosOutroTraballo,
    actualizar_outro_traballo,
    crear_outro_traballo,
    dar_de_baixa_outro_traballo,
    listar_outros_traballos,
)
from horta.services.parcelas import crear_parcela, eliminar_parcela
from horta.services.tarefas import crear_tarefa, facer_tarefa

HOXE = date(2026, 10, 29)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    quen = session.query(Persoa).filter_by(horta_id=horta.id).one()
    return ana, horta, quen


def test_apuntar_editar_e_dar_de_baixa(session):
    ana, horta, quen = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "Leira do río")
    traballo = crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 27), descricion=" Arranxar o peche ",
        parcela_id=parcela.id, persoa_id=quen.id, horas=3), hoxe=HOXE)
    assert (traballo.descricion, traballo.data_fin, traballo.creado_por) == (
        "Arranxar o peche", date(2026, 10, 27), ana.id)
    actualizar_outro_traballo(session, ana, traballo, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 27), data_fin=date(2026, 10, 28),
        descricion="Arranxar o peche", parcela_id=parcela.id, persoa_id=quen.id, horas=5),
        hoxe=HOXE)
    assert (traballo.data_fin, traballo.horas) == (date(2026, 10, 28), 5)
    [no_diario] = [t for t in listar_traballos(session, ana, horta.id, hoxe=HOXE)
                   if t.tipo == "outro_traballo"]
    assert (no_diario.que, no_diario.onde, no_diario.parcelas, no_diario.persoas) == (
        "Arranxar o peche", "Leira do río", frozenset({parcela.id}), (quen.id,))
    dar_de_baixa_outro_traballo(session, ana, traballo)
    assert listar_outros_traballos(session, ana, horta.id) == []
    assert session.get(OutroTraballo, traballo.id).baixa


def test_validacions(session):
    ana, horta, quen = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    alleo = crear_parcela(session, ana, outra.id, "Allea")

    def datos(**cambios):
        return DatosOutroTraballo(**{"horta_id": horta.id, "data_inicio": date(2026, 10, 1),
                                     "descricion": "Limpar", "persoa_id": quen.id, **cambios})

    for cambios, erro in (({"descricion": "  "}, "que traballo"),
                          ({"data_inicio": date(2026, 11, 1)}, "futura"),
                          ({"data_fin": date(2026, 9, 1)}, "anterior"),
                          ({"parcela_id": alleo.id}, "parcela non é desta"),
                          ({"persoa_id": None}, "quen o fixo")):
        with pytest.raises(OperacionNonPermitidaError, match=erro):
            crear_outro_traballo(session, ana, datos(**cambios), hoxe=HOXE)


def test_da_explotacion_enteira(session):
    ana, horta, quen = _escenario(session)
    crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 1), descricion="Levar papeis",
        persoa_id=quen.id), hoxe=HOXE)
    [no_diario] = listar_traballos(session, ana, horta.id, hoxe=HOXE)
    assert (no_diario.tipo, no_diario.que, no_diario.onde, no_diario.parcelas) == (
        "outro_traballo", "Levar papeis", "", frozenset())


def test_tarefa_e_borrados(session):
    ana, horta, quen = _escenario(session)
    parcela = crear_parcela(session, ana, horta.id, "P")
    grupo = crear_animal(session, ana, horta.id, "Galiñas", date(2026, 1, 1), cantidade=5)
    tarefa = crear_tarefa(session, ana, horta.id, "Limpar o galiñeiro", tipo="outro_traballo",
                          animal_id=grupo.id)
    feito = crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 2), descricion=tarefa.descricion,
        animal_id=grupo.id, persoa_id=quen.id), hoxe=HOXE)
    facer_tarefa(session, ana, tarefa, feito)
    assert (tarefa.estado, tarefa.data_feita) == ("feito", date(2026, 10, 2))
    peche = crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 3), descricion="Peche",
        parcela_id=parcela.id, persoa_id=quen.id), hoxe=HOXE)
    # Non é de ningún libro oficial: non impide borrar a parcela, os animais nin a explotación
    eliminar_parcela(session, ana, parcela)
    eliminar_animal(session, ana, grupo)
    assert (peche.parcela_id, feito.animal_id) == (None, None)
    eliminar_horta(session, ana, horta)
    assert session.query(OutroTraballo).count() == 0
