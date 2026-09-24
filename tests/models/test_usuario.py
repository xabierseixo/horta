from horta.models.usuario import RolGlobal, Usuario


def test_crear_e_consultar_usuario(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    atopado = session.query(Usuario).filter_by(email="ana@example.com").one()

    assert atopado.nome == "Ana"
    assert atopado.rol == RolGlobal.USUARIO
    assert atopado.activo is True
    assert atopado.created_at is not None
