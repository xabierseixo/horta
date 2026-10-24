from datetime import date

import pytest

from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.equipo import acceso_da_persoa, conceder_acceso, retirar_acceso, uta_equipo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.persoas import actualizar_persoa, crear_persoa


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


def test_o_creador_entra_no_equipo_ligado_a_sua_conta(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    assert persoa.usuario_id == ana.id
    assert acceso_da_persoa(session, persoa) == RolHorta.ADMIN


def test_conceder_e_retirar_acceso(session):
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Bea")
    conceder_acceso(session, ana, xan, " Bea@Example.com", RolHorta.EDITOR)
    assert acceso_da_persoa(session, xan) == RolHorta.EDITOR
    conceder_acceso(session, ana, xan, "bea@example.com", RolHorta.LECTOR)
    assert acceso_da_persoa(session, xan) == RolHorta.LECTOR
    retirar_acceso(session, ana, xan)
    assert xan.usuario_id is None
    assert session.get(HortaMembro, (horta.id, bea.id)) is None


def test_email_sen_conta_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Xan")
    with pytest.raises(OperacionNonPermitidaError, match="Non hai ningunha conta"):
        conceder_acceso(session, ana, xan, "ninguen@example.com", RolHorta.LECTOR)


def test_unha_conta_non_pode_ir_a_duas_persoas(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Xan")
    with pytest.raises(OperacionNonPermitidaError, match="xa está ligada"):
        conceder_acceso(session, ana, xan, "ana@example.com", RolHorta.ADMIN)


def test_non_se_pode_retirar_o_ultimo_admin(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    with pytest.raises(OperacionNonPermitidaError, match="polo menos un administrador"):
        retirar_acceso(session, ana, persoa)


def test_uta_do_equipo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    persoa = session.query(Persoa).filter_by(horta_id=horta.id).one()
    actualizar_persoa(session, ana, persoa, horas_ano=1920.0, vinculo="titular")
    crear_persoa(session, ana, horta.id, "Xan", horas_ano=960.0, vinculo="asalariado")
    assert uta_equipo(session, ana, horta.id) == 1.5


@pytest.mark.parametrize(
    ("campos", "mensaxe"),
    [
        ({"vinculo": "veciño"}, "Vínculo non válido"),
        ({"horas_ano": 5000.0}, "horas ao ano"),
        ({"xenero": "x"}, "Xénero non válido"),
        ({"data_nacemento": date(2030, 1, 1)}, "data de nacemento"),
    ],
)
def test_validacions_do_equipo(session, campos, mensaxe):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    with pytest.raises(OperacionNonPermitidaError, match=mensaxe):
        crear_persoa(session, ana, horta.id, "Xan", **campos)
