import datetime

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    crear_animal,
    eliminar_animal,
    listar_animais,
)
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro

_DATA_ALTA = datetime.date(2026, 2, 10)


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_admin_da_horta_pode_crear_animal(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    assert animal.id is not None
    assert animal.horta_id == horta.id
    assert animal.estado == "activo"


def test_editor_pode_crear_animal_pero_lector_non(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    crear_animal(session, bea, horta.id, "coellos", _DATA_ALTA)

    with pytest.raises(PermisoDenegadoError):
        crear_animal(session, carlos, horta.id, "coellos", _DATA_ALTA)


def test_lector_pode_listar_pero_non_actualizar_nin_eliminar(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)

    animais = listar_animais(session, carlos, horta.id)
    assert [a.especie for a in animais] == ["galiñas"]

    with pytest.raises(PermisoDenegadoError):
        actualizar_animal(session, carlos, animal, raza="Mos")

    with pytest.raises(PermisoDenegadoError):
        eliminar_animal(session, carlos, animal)


def test_admin_pode_actualizar_e_eliminar_animal(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    actualizado = actualizar_animal(session, ana, animal, raza="Galiña de Mos")
    assert (actualizado.raza, actualizado.cantidade) == ("Galiña de Mos", 6)

    eliminar_animal(session, ana, animal)
    assert listar_animais(session, ana, horta.id) == []


@pytest.mark.parametrize("campo", ["horta_id", "id", "created_at", "campo_inexistente"])
def test_actualizar_animal_rexeita_campos_non_editables(session, campo):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    outra_horta = crear_horta(session, ana, "Outra horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)
    id_orixinal = animal.id

    with pytest.raises(ValueError):
        actualizar_animal(session, ana, animal, cantidade=99, **{campo: outra_horta.id})

    session.refresh(animal)
    assert animal.id == id_orixinal
    assert animal.horta_id == horta.id
    assert animal.cantidade == 6


@pytest.mark.parametrize("cantidade", [0, -2])
def test_cantidade_menor_que_un_ao_crear(session, cantidade):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    with pytest.raises(ValueError, match="A cantidade ten que ser polo menos 1"):
        crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=cantidade)


def test_cantidade_e_baixa_non_se_escriben_a_man(session):
    """Saen das entradas e saídas (services.movementos_animais)."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "galiñas", _DATA_ALTA, cantidade=6)

    for campo, valor in (("cantidade", 8), ("data_baixa", datetime.date(2026, 3, 1)),
                         ("estado", "baixa")):
        with pytest.raises(ValueError, match="non editables"):
            actualizar_animal(session, ana, animal, **{campo: valor})

    session.refresh(animal)
    assert (animal.cantidade, animal.data_baixa, animal.estado) == (6, None, "activo")
