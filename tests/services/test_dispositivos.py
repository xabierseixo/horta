"""Probas do servizo de dispositivos móbiles (app do campo)."""

from __future__ import annotations

import hashlib

import pytest
from sqlalchemy.orm import Session

from horta.models.usuario import RolGlobal, Usuario
from horta.services.dispositivos import (
    crear_dispositivo,
    listar_dispositivos,
    revogar_dispositivo,
    usuario_do_token,
)
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError


def _crear_usuario(session: Session, email: str, activo: bool = True) -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0].capitalize(),
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=activo,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_dispositivo_gardase_con_hash_e_devolve_clave(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")

    disp, clave = crear_dispositivo(session, ana, "  Móbil de Ana  ")

    assert disp.id is not None
    assert disp.usuario_id == ana.id
    assert disp.nome == "Móbil de Ana"
    assert disp.token_hash == hashlib.sha256(clave.encode("utf-8")).hexdigest()
    assert disp.revogado is False
    assert disp.ultimo_uso is None
    assert len(clave) >= 32


def test_crear_dispositivo_sen_nome_falla(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")

    with pytest.raises(OperacionNonPermitidaError, match="Indica o nome"):
        crear_dispositivo(session, ana, "   ")


def test_listar_dispositivos_so_mostra_os_propios(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")

    disp_ana_1, _ = crear_dispositivo(session, ana, "Móbil 1")
    disp_ana_2, _ = crear_dispositivo(session, ana, "Móbil 2")
    disp_bea, _ = crear_dispositivo(session, bea, "Móbil de Bea")

    dispositivos_ana = listar_dispositivos(session, ana)
    ids_ana = {d.id for d in dispositivos_ana}

    assert ids_ana == {disp_ana_1.id, disp_ana_2.id}
    assert disp_bea.id not in ids_ana

    dispositivos_bea = listar_dispositivos(session, bea)
    assert [d.id for d in dispositivos_bea] == [disp_bea.id]


def test_revogar_dispositivo_propio_e_alleo(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    bea = _crear_usuario(session, "bea@example.com")

    disp_ana, _ = crear_dispositivo(session, ana, "Móbil de Ana")

    with pytest.raises(PermisoDenegadoError, match="Non tes permiso"):
        revogar_dispositivo(session, bea, disp_ana)

    revogado = revogar_dispositivo(session, ana, disp_ana)
    assert revogado.revogado is True


def test_usuario_do_token_valido_actualiza_ultimo_uso(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    disp, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    assert disp.ultimo_uso is None

    usuario = usuario_do_token(session, clave)
    assert usuario is not None
    assert usuario.id == ana.id

    session.refresh(disp)
    assert disp.ultimo_uso is not None


def test_usuario_do_token_falso_ou_baleiro_devolve_none(session: Session) -> None:
    assert usuario_do_token(session, "") is None
    assert usuario_do_token(session, "clave-que-non-existe") is None


def test_usuario_do_token_revogado_devolve_none(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    disp, clave = crear_dispositivo(session, ana, "Móbil de Ana")
    revogar_dispositivo(session, ana, disp)

    assert usuario_do_token(session, clave) is None


def test_usuario_do_token_desactivado_devolve_none(session: Session) -> None:
    ana = _crear_usuario(session, "ana@example.com")
    _, clave = crear_dispositivo(session, ana, "Móbil de Ana")

    ana.activo = False
    session.commit()

    assert usuario_do_token(session, clave) is None
