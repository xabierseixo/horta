from horta.models.horta import HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.equipo import aceptar_convite, crear_convite
from horta.services.hortas import crear_horta
from horta.services.persoas import crear_persoa


def _usuario(session, email: str) -> Usuario:
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def test_un_convite_de_lector_non_quita_o_admin(session):
    ana = _usuario(session, "ana@example.com")
    bea = _usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "Explotación")
    session.add(HortaMembro(horta_id=horta.id, usuario_id=bea.id, rol=RolHorta.ADMIN))
    session.commit()
    persoa = crear_persoa(session, ana, horta.id, "Bea")
    convite = crear_convite(session, ana, persoa, RolHorta.LECTOR)
    aceptar_convite(session, convite.token, bea)
    assert session.get(HortaMembro, (horta.id, bea.id)).rol == RolHorta.ADMIN


def test_un_convite_de_editor_sube_a_un_lector(session):
    ana = _usuario(session, "ana@example.com")
    bea = _usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "Explotación")
    session.add(HortaMembro(horta_id=horta.id, usuario_id=bea.id, rol=RolHorta.LECTOR))
    session.commit()
    persoa = crear_persoa(session, ana, horta.id, "Bea")
    convite = crear_convite(session, ana, persoa, RolHorta.EDITOR)
    aceptar_convite(session, convite.token, bea)
    assert session.get(HortaMembro, (horta.id, bea.id)).rol == RolHorta.EDITOR
