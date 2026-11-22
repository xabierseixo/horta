from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario


def test_crear_horta_e_membro(session):
    usuario = Usuario(
        nome="Ana",
        email="ana@example.com",
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()

    horta = Horta(nome="A miña horta", uso_profesional=False)
    session.add(horta)
    session.flush()

    membro = HortaMembro(horta_id=horta.id, usuario_id=usuario.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.commit()

    atopado = session.get(HortaMembro, (horta.id, usuario.id))
    assert atopado is not None
    assert atopado.rol == RolHorta.ADMIN
