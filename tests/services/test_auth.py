from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import (
    autenticar,
    hash_password,
    obter_usuario_activo,
    verify_password,
)


def test_hash_password_non_garda_texto_plano():
    hashed = hash_password("contrasinal123")
    assert hashed != "contrasinal123"


def test_verify_password_acepta_contrasinal_correcto():
    hashed = hash_password("contrasinal123")
    assert verify_password("contrasinal123", hashed) is True


def test_verify_password_rexeita_contrasinal_incorrecto():
    hashed = hash_password("contrasinal123")
    assert verify_password("outra-cousa", hashed) is False


def test_autenticar_con_credenciais_correctas(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    resultado = autenticar(session, "ana@example.com", "segredo")

    assert resultado is not None
    assert resultado.email == "ana@example.com"


def test_autenticar_con_contrasinal_incorrecto(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "ana@example.com", "incorrecto") is None


def test_autenticar_usuario_inactivo(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=False,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "ana@example.com", "segredo") is None


def test_autenticar_email_inexistente(session):
    assert autenticar(session, "non-existe@example.com", "calquera") is None


def test_obter_usuario_activo_devolve_usuario_activo(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    resultado = obter_usuario_activo(session, usuario.id)

    assert resultado is not None
    assert resultado.id == usuario.id


def test_obter_usuario_activo_devolve_none_se_inactivo(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=False,
    )
    session.add(usuario)
    session.commit()

    assert obter_usuario_activo(session, usuario.id) is None


def test_obter_usuario_activo_devolve_none_se_non_existe(session):
    assert obter_usuario_activo(session, 9999) is None

def test_autenticar_ignora_maiusculas_e_espazos(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    assert autenticar(session, "  Ana@Example.COM ", "segredo") is not None
