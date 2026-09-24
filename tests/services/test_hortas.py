import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import (
    cambiar_rol_membro,
    crear_horta,
    engadir_membro,
    listar_hortas_usuario,
    quitar_membro,
)


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


def test_crear_horta_fai_ao_creador_admin_da_horta(session):
    ana = _crear_usuario(session, "ana@example.com")

    horta = crear_horta(session, ana, "A miña horta")

    [(horta_listada, rol)] = listar_hortas_usuario(session, ana)
    assert horta_listada.id == horta.id
    assert rol == RolHorta.ADMIN


def test_admin_da_horta_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")

    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    hortas_de_bea = listar_hortas_usuario(session, bea)
    assert hortas_de_bea == [(horta, RolHorta.EDITOR)]


def test_non_admin_non_pode_engadir_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.EDITOR)

    with pytest.raises(PermisoDenegadoError):
        engadir_membro(session, bea, horta.id, carlos, RolHorta.LECTOR)


def test_admin_pode_cambiar_rol_e_quitar_membro(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, bea, RolHorta.LECTOR)

    cambiar_rol_membro(session, ana, horta.id, bea.id, RolHorta.EDITOR)
    assert listar_hortas_usuario(session, bea) == [(horta, RolHorta.EDITOR)]

    quitar_membro(session, ana, horta.id, bea.id)
    assert listar_hortas_usuario(session, bea) == []


def test_usuario_sen_relacion_non_ve_a_horta(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    crear_horta(session, ana, "A miña horta")

    assert listar_hortas_usuario(session, carlos) == []
