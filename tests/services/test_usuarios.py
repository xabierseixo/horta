import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.usuarios import (
    activar_usuario,
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


def test_admin_pode_reactivar_usuario(session):
    admin = _crear_admin(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")
    desactivar_usuario(session, admin, usuario)

    reactivado = activar_usuario(session, admin, usuario)

    assert reactivado.activo is True


def test_usuario_normal_non_pode_activar_nin_desactivar(session):
    admin = _crear_admin(session)
    normal = _crear_usuario_normal(session)
    usuario = crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal")

    with pytest.raises(PermisoDenegadoError):
        desactivar_usuario(session, normal, usuario)
    with pytest.raises(PermisoDenegadoError):
        activar_usuario(session, normal, usuario)


def test_admin_non_pode_desactivarse_a_si_mesmo(session):
    admin = _crear_admin(session)

    with pytest.raises(OperacionNonPermitidaError):
        desactivar_usuario(session, admin, admin)

    session.refresh(admin)
    assert admin.activo is True


def test_non_se_pode_quitar_o_rol_ao_ultimo_admin_activo(session):
    admin = _crear_admin(session)

    with pytest.raises(OperacionNonPermitidaError):
        actualizar_usuario(session, admin, admin, rol=RolGlobal.USUARIO)

    session.refresh(admin)
    assert admin.rol == RolGlobal.ADMIN


def test_admin_pode_quitarse_o_rol_se_hai_outro_admin_activo(session):
    admin = _crear_admin(session)
    crear_usuario(session, admin, "Bea", "bea@example.com", "contrasinal", rol=RolGlobal.ADMIN)

    actualizado = actualizar_usuario(session, admin, admin, rol=RolGlobal.USUARIO)

    assert actualizado.rol == RolGlobal.USUARIO


def test_un_admin_inactivo_non_conta_como_admin_restante(session):
    admin = _crear_admin(session)
    bea = crear_usuario(
        session, admin, "Bea", "bea@example.com", "contrasinal", rol=RolGlobal.ADMIN
    )
    desactivar_usuario(session, admin, bea)

    with pytest.raises(OperacionNonPermitidaError):
        actualizar_usuario(session, admin, admin, rol=RolGlobal.USUARIO)
