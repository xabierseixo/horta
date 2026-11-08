from __future__ import annotations

import json

import pytest
from sqlalchemy.orm import Session

from horta.models.horta import HortaMembro, RolHorta
from horta.models.legal import ConfiguracionLegal
from horta.models.persoa import Persoa
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.legal import (
    VERSION_POLITICA,
    aceptar_politica,
    borrar_minha_conta,
    exportar_meus_datos,
    gardar_configuracion,
    precisa_aceptar,
    texto_legal,
)


def _crear_admin(session: Session, email: str = "admin@example.com") -> Usuario:
    admin = Usuario(
        nome="Admin",
        email=email,
        password_hash=hash_password("segredo"),
        rol=RolGlobal.ADMIN,
        activo=True,
    )
    session.add(admin)
    session.commit()
    return admin


def _crear_usuario(session: Session, email: str = "usuario@example.com") -> Usuario:
    usuario = Usuario(
        nome=email.split("@")[0],
        email=email,
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_texto_legal_sen_configuracion(session: Session) -> None:
    for cal in ("aviso", "privacidade"):
        txt = texto_legal(session, cal)
        assert "(pendente de configurar)" in txt
        assert "{" not in txt
        assert "}" not in txt
        assert "Delegado de protección de datos" not in txt


def test_texto_legal_con_configuracion(session: Session) -> None:
    admin = _crear_admin(session)
    gardar_configuracion(
        session,
        admin,
        nome="Agro Galicia S.L.",
        nif="B12345678",
        correo="info@agrogalicia.gal",
    )

    txt_aviso = texto_legal(session, "aviso")
    assert "Agro Galicia S.L." in txt_aviso
    assert "B12345678" in txt_aviso
    assert "info@agrogalicia.gal" in txt_aviso
    assert "Delegado de protección de datos" not in txt_aviso

    txt_priv = texto_legal(session, "privacidade")
    assert "Agro Galicia S.L." in txt_priv
    assert "B12345678" in txt_priv
    assert "Delegado de protección de datos" not in txt_priv


def test_texto_legal_con_dpd_e_localizacion(session: Session) -> None:
    admin = _crear_admin(session)
    gardar_configuracion(
        session,
        admin,
        dpd="dpd@agrogalicia.gal",
        localizacion="Servidores en Santiago de Compostela.",
    )

    txt = texto_legal(session, "privacidade")
    assert "- **Delegado de protección de datos:** dpd@agrogalicia.gal" in txt
    assert "Servidores en Santiago de Compostela." in txt


def test_texto_legal_desconhecido(session: Session) -> None:
    with pytest.raises(ValueError):
        texto_legal(session, "outro")


def test_gardar_configuracion_permisos(session: Session) -> None:
    normal = _crear_usuario(session, "normal@example.com")
    with pytest.raises(PermisoDenegadoError):
        gardar_configuracion(session, normal, nome="Horta")


def test_gardar_configuracion_actualiza_mesma_fila(session: Session) -> None:
    admin = _crear_admin(session)
    conf1 = gardar_configuracion(session, admin, nome="Nome 1", nif="111")
    assert conf1.nome == "Nome 1"

    conf2 = gardar_configuracion(session, admin, nome="Nome 2")
    assert conf2.id == conf1.id
    assert conf2.nome == "Nome 2"
    assert conf2.nif == "111"
    assert conf2.actualizado_en is not None

    assert session.query(ConfiguracionLegal).count() == 1


def test_gardar_configuracion_campo_desconhecido(session: Session) -> None:
    admin = _crear_admin(session)
    with pytest.raises(ValueError):
        gardar_configuracion(session, admin, campo_inventado="valor")


def test_precisa_aceptar_e_aceptar_politica(session: Session) -> None:
    u = _crear_usuario(session, "pepe@example.com")
    assert precisa_aceptar(u) is True

    aceptar_politica(session, u)
    assert precisa_aceptar(u) is False
    assert u.politica_version == VERSION_POLITICA
    assert u.politica_aceptada_en is not None


def test_exportar_meus_datos(session: Session) -> None:
    u = _crear_usuario(session, "xoan@example.com")
    horta = crear_horta(session, u, "Horta de Xoán")
    persoa = session.query(Persoa).filter_by(usuario_id=u.id).first()
    assert persoa is not None

    dados_bytes = exportar_meus_datos(session, u)
    assert isinstance(dados_bytes, bytes)
    assert b"password_hash" not in dados_bytes

    dados = json.loads(dados_bytes.decode("utf-8"))
    assert "conta" in dados
    assert "explotacions" in dados
    assert "persoas" in dados

    assert dados["conta"]["email"] == "xoan@example.com"
    assert any(exp["id"] == horta.id for exp in dados["explotacions"])
    assert any(p["id"] == persoa.id for p in dados["persoas"])


def test_borrar_minha_conta_caso_normal(session: Session) -> None:
    u = _crear_usuario(session, "borrame@example.com")
    crear_horta(session, u, "Horta Solitaria")
    persoa = session.query(Persoa).filter_by(usuario_id=u.id).first()
    assert persoa is not None
    uid = u.id

    borrar_minha_conta(session, u)

    # Membro borrado
    assert session.query(HortaMembro).filter_by(usuario_id=uid).count() == 0

    # A persoa consérvase con usuario_id a None
    session.refresh(persoa)
    assert persoa.usuario_id is None

    # Usuario anonimizado e inactivo
    session.refresh(u)
    assert u.nome == "Conta borrada"
    assert u.email == f"borrada-{uid}@invalido.local"
    assert u.activo is False


def test_borrar_minha_conta_unico_admin_con_outros_membros(session: Session) -> None:
    u1 = _crear_usuario(session, "admin_coop@example.com")
    u2 = _crear_usuario(session, "socio_coop@example.com")
    horta = crear_horta(session, u1, "Cooperativa")
    engadir_membro(session, u1, horta.id, u2, RolHorta.LECTOR)

    with pytest.raises(OperacionNonPermitidaError) as exc_info:
        borrar_minha_conta(session, u1)

    assert "Cooperativa" in str(exc_info.value)

    # Nada cambia
    session.refresh(u1)
    assert u1.activo is True
    assert u1.email == "admin_coop@example.com"
    assert session.query(HortaMembro).filter_by(usuario_id=u1.id).count() == 1


def test_borrar_minha_conta_ultimo_admin_global(session: Session) -> None:
    admin = _crear_admin(session, "superadmin@example.com")
    with pytest.raises(OperacionNonPermitidaError):
        borrar_minha_conta(session, admin)

    session.refresh(admin)
    assert admin.activo is True


def test_borrar_minha_conta_admin_global_se_hai_outro(session: Session) -> None:
    _crear_admin(session, "admin1@example.com")
    admin2 = _crear_admin(session, "admin2@example.com")

    borrar_minha_conta(session, admin2)
    session.refresh(admin2)
    assert admin2.activo is False
    assert admin2.nome == "Conta borrada"


def test_aviso_legal_inclue_licenza_e_codigo_fonte(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("HORTA_CODIGO_FONTE", raising=False)
    texto = texto_legal(session, "aviso")
    assert "AGPL-3.0-or-later" in texto
    assert "https://github.com/xabierseixo/horta" in texto
    monkeypatch.setenv("HORTA_CODIGO_FONTE", "https://exemplo.gal/codigo")
    assert "https://exemplo.gal/codigo" in texto_legal(session, "aviso")
