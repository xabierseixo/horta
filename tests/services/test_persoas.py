from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.persoas import actualizar_persoa, crear_persoa, listar_persoas, ropo_vixente


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(nome=email.split("@")[0], email=email, password_hash="hash-falso",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_aplicador_con_ropo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan", apelidos="Pérez", nif="12345678z",
                          papeis={"aplicador"}, ropo_numero="1234567890",
                          ropo_caducidade=date(2027, 5, 1))
    assert persoa.nif == "12345678Z"
    assert "Xan" in [p.nome for p in listar_persoas(session, ana, horta.id)]


def test_aplicador_sen_ropo_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="nº ROPO e a data de caducidade"):
        crear_persoa(session, ana, horta.id, "Xan", papeis={"aplicador"})


def test_nif_mal_formado_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="NIF non é válido"):
        crear_persoa(session, ana, horta.id, "Xan", nif="123")


def test_lector_non_pode_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_persoa(session, carlos, horta.id, "Xan")


def test_ropo_vixente_ata_o_dia_de_caducidade_incluido(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan", papeis={"aplicador"}, ropo_numero="1",
                          ropo_caducidade=date(2026, 6, 1))
    assert ropo_vixente(persoa, date(2026, 6, 1)) is True
    assert ropo_vixente(persoa, date(2026, 6, 2)) is False


def test_desactivar_persoa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan")
    actualizar_persoa(session, ana, persoa, activa=False)
    assert [p.nome for p in listar_persoas(session, ana, horta.id)] == ["ana"]
    assert len(listar_persoas(session, ana, horta.id, so_activas=False)) == 2
