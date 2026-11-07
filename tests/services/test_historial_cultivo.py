"""Historial dun cultivo (servizo)."""

from datetime import date

import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.colleitas import DatosColleita, crear_colleita
from horta.services.cultivos import actualizar_cultivo, crear_cultivo
from horta.services.errors import PermisoDenegadoError
from horta.services.historial import historial_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela
from horta.services.regas import DatosRega, crear_rega

# A persoa que crear_horta engade por quen crea a explotación (a primeira da BD)
QUEN = 1

HOXE = date(2026, 10, 26)


def _escenario(session):
    ana = Usuario(
        nome="ana", email="ana@example.com", password_hash="x",
        rol=RolGlobal.USUARIO, activo=True
    )
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "Horta de abaixo")
    cultivo1 = crear_cultivo(session, ana, parcela.id, "Tomate")
    cultivo2 = crear_cultivo(session, ana, parcela.id, "Pemento")
    actualizar_cultivo(
        session, ana, cultivo1, data_inicio=date(2026, 5, 1), tipo_inicio="plantacion"
    )
    actualizar_cultivo(
        session, ana, cultivo2, data_inicio=date(2026, 5, 10), tipo_inicio="plantacion"
    )
    return ana, horta, parcela, cultivo1, cultivo2


def test_historial_cultivo(session):
    ana, _, _, c1, c2 = _escenario(session)
    crear_rega(
        session,
        ana,
        DatosRega(cultivo_id=c1.id, data_inicio=date(2026, 7, 1), persoa_id=QUEN),
        hoxe=HOXE,
    )
    crear_colleita(
        session,
        ana,
        DatosColleita(
            cultivo_id=c1.id,
            data=date(2026, 8, 1),
            cantidade=50.0,
            unidade="kg",
            lote="2026-TOMATE-001",
            persoa_id=QUEN,
        ),
        hoxe=HOXE,
    )

    historial1 = historial_cultivo(session, ana, c1)
    tipos1 = [t.tipo for t in historial1]
    assert tipos1 == ["colleita", "rega", "sementeira"]
    assert all(c1.id in t.cultivos for t in historial1)

    historial2 = historial_cultivo(session, ana, c2)
    tipos2 = [t.tipo for t in historial2]
    assert "rega" not in tipos2
    assert "colleita" not in tipos2
    assert tipos2 == ["sementeira"]
    assert all(c2.id in t.cultivos for t in historial2)


def test_historial_cultivo_sen_rol_denega_permiso(session):
    ana, _, _, c1, _ = _escenario(session)
    outro = Usuario(
        nome="outro", email="outro@example.com", password_hash="x",
        rol=RolGlobal.USUARIO, activo=True
    )
    session.add(outro)
    session.commit()
    with pytest.raises(PermisoDenegadoError):
        historial_cultivo(session, outro, c1)
