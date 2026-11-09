"""Probas de acceso para inspección e auditoría (tarefa 182b)."""

from datetime import date, datetime, timedelta

import pytest

from horta.models.acceso import RexistroAcceso
from horta.models.horta import HortaMembro, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.accesos import listar_accesos, rexistrar_acceso
from horta.services.equipo import aceptar_convite, crear_convite
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import (
    comprobar_rol_horta,
    crear_horta,
    engadir_membro,
    listar_hortas_usuario,
)
from horta.services.persoas import crear_persoa


def _crear_usuario(session, email: str, nome: str | None = None) -> Usuario:
    usuario = Usuario(
        nome=nome or email.split("@")[0].capitalize(),
        email=email,
        password_hash="hash-falso",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    return usuario


def test_convite_con_data_e_rol_non_lector_falla(session):
    admin = _crear_usuario(session, "admin@example.com")
    horta = crear_horta(session, admin, "Explotación Proba")
    persoa = crear_persoa(session, admin, horta.id, "Inspector Xunta")

    data_futura = date.today() + timedelta(days=30)
    data_pasada = date.today() - timedelta(days=1)

    # Rol non lector con data de fin falla
    with pytest.raises(OperacionNonPermitidaError, match="só lectura"):
        crear_convite(
            session, admin, persoa, RolHorta.EDITOR, acceso_ata=data_futura, motivo="inspeccion"
        )

    with pytest.raises(OperacionNonPermitidaError, match="só lectura"):
        crear_convite(
            session, admin, persoa, RolHorta.ADMIN, acceso_ata=data_futura, motivo="auditoria"
        )

    # Data de fin pasada falla
    with pytest.raises(OperacionNonPermitidaError, match="anterior a hoxe"):
        crear_convite(
            session, admin, persoa, RolHorta.LECTOR, acceso_ata=data_pasada, motivo="certificacion"
        )

    # Motivo descoñecido falla
    with pytest.raises(OperacionNonPermitidaError, match="Motivo de acceso non válido"):
        crear_convite(
            session, admin, persoa, RolHorta.LECTOR, acceso_ata=data_futura, motivo="inventado"
        )

    # Convite válido con rol LECTOR e data futura
    convite = crear_convite(
        session, admin, persoa, RolHorta.LECTOR, acceso_ata=data_futura, motivo="inspeccion"
    )
    assert convite.rol == RolHorta.LECTOR
    assert convite.acceso_ata == data_futura
    assert convite.motivo == "inspeccion"


def test_aceptar_convite_copia_acceso_ata(session):
    admin = _crear_usuario(session, "admin2@example.com")
    horta = crear_horta(session, admin, "Explotación Proba 2")
    persoa = crear_persoa(session, admin, horta.id, "Auditora GlobalGAP")

    data_fin = date.today() + timedelta(days=60)
    convite = crear_convite(
        session, admin, persoa, RolHorta.LECTOR, acceso_ata=data_fin, motivo="auditoria"
    )

    auditora = _crear_usuario(session, "auditora@example.com")
    aceptar_convite(session, convite.token, auditora)

    membro = session.get(HortaMembro, (horta.id, auditora.id))
    assert membro is not None
    assert membro.rol == RolHorta.LECTOR
    assert membro.acceso_ata == data_fin


def test_membro_con_acceso_rematado_non_pasa_comprobar_rol_horta_e_non_sae_na_lista(session):
    admin = _crear_usuario(session, "admin3@example.com")
    horta = crear_horta(session, admin, "Explotación Proba 3")

    inspector = _crear_usuario(session, "inspector@example.com")
    data_rematada = date(2026, 1, 15)

    # Engadimos membro con acceso rematado
    membro = engadir_membro(session, admin, horta.id, inspector, RolHorta.LECTOR)
    membro.acceso_ata = data_rematada
    session.commit()

    # comprobar_rol_horta ten que denegar o permiso co texto exacto requirido
    with pytest.raises(
        PermisoDenegadoError, match="O teu acceso a esta explotación rematou o 15/01/2026"
    ):
        comprobar_rol_horta(session, horta.id, inspector, {RolHorta.LECTOR})

    # listar_hortas_usuario non devolve a explotación
    hortas_listadas = listar_hortas_usuario(session, inspector)
    assert horta.id not in [h.id for h, _ in hortas_listadas]

    # Con data futura si ten acceso e sae na lista
    data_activa = date.today() + timedelta(days=10)
    membro.acceso_ata = data_activa
    session.commit()

    membro_ok = comprobar_rol_horta(session, horta.id, inspector, {RolHorta.LECTOR})
    assert membro_ok.rol == RolHorta.LECTOR
    hortas_listadas_activa = listar_hortas_usuario(session, inspector)
    assert horta.id in [h.id for h, _ in hortas_listadas_activa]


def test_rexistro_so_garda_accesos_con_data_de_fin(session):
    admin = _crear_usuario(session, "admin4@example.com")
    horta = crear_horta(session, admin, "Explotación Proba 4")

    # Traballador diario sen data de fin
    traballador = _crear_usuario(session, "traballador@example.com")
    engadir_membro(session, admin, horta.id, traballador, RolHorta.EDITOR)

    # Acceso do traballador diario: non debe rexistrarse
    resultado_traballador = rexistrar_acceso(session, traballador, horta.id, "resumo")
    assert resultado_traballador is None
    assert session.query(RexistroAcceso).count() == 0

    # Auditor con data de fin
    auditor = _crear_usuario(session, "auditor_cert@example.com", nome="Auditor Certificación")
    membro_auditor = engadir_membro(session, admin, horta.id, auditor, RolHorta.LECTOR)
    membro_auditor.acceso_ata = date.today() + timedelta(days=5)
    session.commit()

    # Acceso do auditor: si debe rexistrarse
    agora = datetime(2026, 11, 9, 10, 30, 0)
    resultado_auditor = rexistrar_acceso(
        session, auditor, horta.id, "cultivos", agora=agora
    )
    assert resultado_auditor is not None
    assert resultado_auditor.horta_id == horta.id
    assert resultado_auditor.usuario_id == auditor.id
    assert resultado_auditor.seccion == "cultivos"
    assert resultado_auditor.data_hora == agora

    assert session.query(RexistroAcceso).count() == 1


def test_listar_accesos_so_para_admin(session):
    admin = _crear_usuario(session, "admin5@example.com")
    horta = crear_horta(session, admin, "Explotación Proba 5")

    editor = _crear_usuario(session, "editor5@example.com")
    engadir_membro(session, admin, horta.id, editor, RolHorta.EDITOR)

    lector = _crear_usuario(session, "lector5@example.com")
    engadir_membro(session, admin, horta.id, lector, RolHorta.LECTOR)

    auditor = _crear_usuario(session, "auditor5@example.com", nome="Auditor Xeral")
    membro_auditor = engadir_membro(session, admin, horta.id, auditor, RolHorta.LECTOR)
    membro_auditor.acceso_ata = date.today() + timedelta(days=15)
    session.commit()

    t1 = datetime(2026, 11, 9, 9, 0, 0)
    t2 = datetime(2026, 11, 9, 9, 15, 0)
    rexistrar_acceso(session, auditor, horta.id, "cultivos", agora=t1)
    rexistrar_acceso(session, auditor, horta.id, "parcelas", agora=t2)

    # Usuarios non admin non poden listar accesos
    with pytest.raises(PermisoDenegadoError):
        listar_accesos(session, editor, horta.id)

    with pytest.raises(PermisoDenegadoError):
        listar_accesos(session, lector, horta.id)

    with pytest.raises(PermisoDenegadoError):
        listar_accesos(session, auditor, horta.id)

    alleo = _crear_usuario(session, "alleo@example.com")
    with pytest.raises(PermisoDenegadoError):
        listar_accesos(session, alleo, horta.id)

    # Admin si pode listar: máis recente primeiro
    accesos = listar_accesos(session, admin, horta.id)
    assert len(accesos) == 2
    assert accesos[0].seccion == "parcelas"
    assert accesos[0].data_hora == t2
    assert accesos[0].conta == "Auditor Xeral"
    assert accesos[1].seccion == "cultivos"
    assert accesos[1].data_hora == t1
    assert accesos[1].conta == "Auditor Xeral"
