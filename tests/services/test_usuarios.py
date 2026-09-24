import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import PermisoDenegadoError
from horta.services.usuarios import (
    actualizar_usuario,
    crear_usuario,
    desactivar_usuario,
    listar_usuarios,
)


def _crear_admin(session) -> Usuario:
    admin = Usuario(
        nome="Admin",
        email="admin@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.ADMIN,
        activo=True,
    )
    session.add(admin)
    session.commit()
    return admin


def _crear_usuario_normal(session) -> Usuario:
    normal = Usuario(
        nome="Normal",
        email="normal@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(normal)
    session.commit()
    return normal


def test_admin_pode_crear_usuario(session):
    admin = _crear_admin(session)

    novo = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    assert novo.id is not None
    assert novo.rol == RolGlobal.USUARIO
    assert novo.activo is True


def test_usuario_normal_non_pode_crear_usuario(session):
    normal = _crear_usuario_normal(session)

    with pytest.raises(PermisoDenegadoError):
        crear_usuario(session, normal, "Bea", "bea@example.com", "contrasinal")


def test_admin_pode_actualizar_usuario(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    actualizado = actualizar_usuario(session, admin, usuario, nome="Beatriz", rol=RolGlobal.ADMIN)

    assert actualizado.nome == "Beatriz"
    assert actualizado.rol == RolGlobal.ADMIN


def test_admin_pode_desactivar_usuario(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    desactivado = desactivar_usuario(session, admin, usuario)

    assert desactivado.activo is False


def test_listar_usuarios_require_admin(session):
    admin = _crear_admin(session)
    normal = _crear_usuario_normal(session)
    crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    usuarios = listar_usuarios(session, admin)
    assert {u.email for u in usuarios} == {
        "admin@example.com",
        "normal@example.com",
        "bea@example.com",
    }

    with pytest.raises(PermisoDenegadoError):
        listar_usuarios(session, normal)
