import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.usuarios import crear_usuario
from horta.ui import accions


@pytest.fixture()
def notificacions(monkeypatch):
    rexistradas: list[tuple[str, str | None]] = []
    monkeypatch.setattr(
        accions.ui, "notify", lambda mensaxe, type=None, **_: rexistradas.append((mensaxe, type))
    )
    return rexistradas


def _crear_admin(session) -> Usuario:
    admin = Usuario(
        nome="Admin",
        email="admin@example.com",
        password_hash="hash-falso",
        rol=RolGlobal.ADMIN,
        activo=True,
    )
    session.add(admin)
    session.commit()
    return admin


def test_executar_accion_devolve_true_se_vai_ben(session, notificacions):
    assert accions.executar_accion(session, lambda: None) is True
    assert notificacions == []


@pytest.mark.parametrize(
    "erro", [PermisoDenegadoError("sen permiso"), OperacionNonPermitidaError("non se pode")]
)
def test_executar_accion_notifica_erros_de_dominio(session, notificacions, erro):
    def accion() -> None:
        raise erro

    assert accions.executar_accion(session, accion) is False
    assert notificacions == [(str(erro), "negative")]


def test_executar_accion_notifica_duplicado_e_fai_rollback(session, notificacions):
    admin = _crear_admin(session)

    resultado = accions.executar_accion(
        session,
        lambda: crear_usuario(session, admin, "Outro", "admin@example.com", "contrasinal"),
    )

    assert resultado is False
    assert notificacions == [("Xa existe un rexistro con eses datos", "negative")]
    # A sesión segue usable despois do rollback.
    assert session.query(Usuario).count() == 1
