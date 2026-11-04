from datetime import date

import pytest

from horta.models.animal import Animal
from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    crear_animal,
    crear_identificado,
    eliminar_animal,
    listar_animais,
    ten_identificados,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta

_DATA_ALTA = date(2026, 2, 10)


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


def test_grupo_con_animal_identificado_non_se_borra(session):
    """Un grupo con crotais (animais identificados) debe conservarse e rexeitar o borrado."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "Vacas", _DATA_ALTA, cantidade=2)

    crear_identificado(
        session,
        ana,
        animal,
        identificador="ES012345678901",
        data_alta=_DATA_ALTA,
        dispositivo="crotal",
    )

    assert ten_identificados(session, animal.id)

    with pytest.raises(
        OperacionNonPermitidaError,
        match="animais identificados.*debe conservarse",
    ):
        eliminar_animal(session, ana, animal)

    # O grupo non se borrou da base de datos
    session.refresh(animal)
    assert session.get(Animal, animal.id) is not None
    assert len(listar_animais(session, ana, horta.id)) == 1


def test_grupo_con_identificado_dado_de_baixa_tampouco_se_borra(session):
    """Mesmo se o animal identificado ten data de baixa, o historial do libro gandeiro
    debe conservarse e o grupo non pode eliminarse."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "Ovellas", _DATA_ALTA, cantidade=1)

    crear_identificado(
        session,
        ana,
        animal,
        identificador="ES098765432109",
        data_alta=_DATA_ALTA,
        data_baixa=date(2026, 3, 1),
        dispositivo="crotal",
    )

    assert ten_identificados(session, animal.id)

    with pytest.raises(
        OperacionNonPermitidaError,
        match="animais identificados.*debe conservarse",
    ):
        eliminar_animal(session, ana, animal)

    assert session.get(Animal, animal.id) is not None


def test_grupo_sen_nada_borrase(session):
    """Un grupo sen animais identificados nin rexistros bórrase sen problema."""
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    animal = crear_animal(session, ana, horta.id, "Galiñas", _DATA_ALTA, cantidade=6)

    assert not ten_identificados(session, animal.id)

    eliminar_animal(session, ana, animal)

    assert session.get(Animal, animal.id) is None
    assert listar_animais(session, ana, horta.id) == []
