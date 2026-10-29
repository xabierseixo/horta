"""Usuarios, Equipo e Contactos (deseño global §2bis): convites, duplicados, xuntar e historial."""

from datetime import date, datetime, timedelta

import pytest

from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import verify_password
from horta.services.equipo import (
    acceso_da_persoa,
    aceptar_convite,
    cambiar_permiso,
    crear_conta_con_convite,
    crear_convite,
    duplicados,
    historial,
    xuntar_persoas,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import crear_horta
from horta.services.outros_traballos import DatosOutroTraballo, crear_outro_traballo
from horta.services.persoas import crear_contacto, crear_persoa

AGORA = datetime(2026, 10, 29, 12, 0)


def _usuario(session, email):
    u = Usuario(nome=email.split("@")[0], email=email, password_hash="x",
                rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _escenario(session):
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Explotación")
    xan = crear_persoa(session, ana, horta.id, "Xan", papeis={"traballador"})
    return ana, horta, xan


def test_convite_crea_a_conta_co_seu_contrasinal(session):
    ana, horta, xan = _escenario(session)
    convite = crear_convite(session, ana, xan, RolHorta.EDITOR, AGORA)
    conta = crear_conta_con_convite(session, convite.token, " Xan@Example.com", "segredo-1",
                                    AGORA)
    assert (conta.email, verify_password("segredo-1", conta.password_hash)) == (
        "xan@example.com", True)
    assert (xan.usuario_id, acceso_da_persoa(session, xan)) == (conta.id, RolHorta.EDITOR)
    # Xa usado
    with pytest.raises(OperacionNonPermitidaError, match="non vale"):
        crear_conta_con_convite(session, convite.token, "outro@example.com", "segredo-1", AGORA)
    cambiar_permiso(session, ana, xan, RolHorta.LECTOR)
    assert acceso_da_persoa(session, xan) == RolHorta.LECTOR


def test_convite_con_conta_que_xa_existe_e_caducidade(session):
    ana, horta, xan = _escenario(session)
    bea = _usuario(session, "bea@example.com")
    vello = crear_convite(session, ana, xan, RolHorta.LECTOR, AGORA).token
    novo = crear_convite(session, ana, xan, RolHorta.EDITOR, AGORA).token
    # Só vale o último
    with pytest.raises(OperacionNonPermitidaError, match="non vale"):
        aceptar_convite(session, vello, bea, AGORA)
    with pytest.raises(OperacionNonPermitidaError, match="non vale"):
        aceptar_convite(session, novo, bea, AGORA + timedelta(days=8))
    with pytest.raises(OperacionNonPermitidaError, match="Xa hai unha conta"):
        crear_conta_con_convite(session, novo, "bea@example.com", "segredo-1", AGORA)
    aceptar_convite(session, novo, bea, AGORA)
    assert session.get(HortaMembro, (horta.id, bea.id)).rol == RolHorta.EDITOR
    # A conta de Ana xa está na explotación como outra persoa
    outra = crear_persoa(session, ana, horta.id, "Outra", papeis={"traballador"})
    with pytest.raises(OperacionNonPermitidaError, match="xa está nesta explotación"):
        aceptar_convite(session, crear_convite(session, ana, outra, RolHorta.LECTOR, AGORA).token,
                        ana, AGORA)


def test_duplicados_e_xuntar(session):
    ana, horta, _ = _escenario(session)
    eu = session.query(Persoa).filter_by(horta_id=horta.id, usuario_id=ana.id).one()
    titular = crear_persoa(session, ana, horta.id, "Ana", apelidos="Souto", nif="11111111H",
                           papeis={"titular"})
    assert duplicados(session, horta.id, "ana", None, None, "ANA@example.com") == [eu]
    assert duplicados(session, horta.id, "X", None, "11111111h", None) == [titular]
    assert duplicados(session, horta.id, "Ana", "Souto", None, None, excepto=titular.id) == []
    crear_outro_traballo(session, ana, DatosOutroTraballo(
        horta_id=horta.id, data_inicio=date(2026, 10, 1), descricion="Peche",
        persoa_id=eu.id), hoxe=date(2026, 10, 29))
    xuntar_persoas(session, ana, titular, eu)
    assert (titular.usuario_id, titular.papeis, titular.email) == (
        ana.id, {"titular", "traballador"}, "ana@example.com")
    assert acceso_da_persoa(session, titular) == RolHorta.ADMIN
    assert session.get(Persoa, eu.id) is None
    assert [(f.que, f.data) for f in historial(session, ana, titular)] == [
        ("Outro traballo", date(2026, 10, 1))]


def test_historial_dun_contacto(session):
    ana, horta, _ = _escenario(session)
    coop = crear_contacto(session, ana, horta.id, "Coop", "provedor", tipo="entidade")
    assert historial(session, ana, coop) == []
    with pytest.raises(OperacionNonPermitidaError, match="distintas"):
        xuntar_persoas(session, ana, coop, coop)
