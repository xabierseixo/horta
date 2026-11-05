from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta


def _usuario(session) -> Usuario:
    u = Usuario(nome="Ana", email="ana@example.com", password_hash="x",
                rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _papeis(session, horta_id: int) -> set[str]:
    persoa = session.query(Persoa).filter_by(horta_id=horta_id).one()
    return {p.papel for p in persoa.papeis_rexistro}


def test_quen_crea_e_titular_se_o_di(session):
    horta = crear_horta(session, _usuario(session), "Explotación", son_titular=True)
    assert _papeis(session, horta.id) == {"titular", "traballador"}


def test_por_defecto_so_traballador(session):
    horta = crear_horta(session, _usuario(session), "Explotación")
    assert _papeis(session, horta.id) == {"traballador"}
