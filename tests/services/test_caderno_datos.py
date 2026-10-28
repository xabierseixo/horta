from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.usuario import RolGlobal, Usuario
from horta.services.caderno import xerar_caderno
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import actualizar_horta, crear_horta
from horta.services.maquinaria import crear_maquina
from horta.services.persoas import crear_persoa


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta da Ana")
    actualizar_horta(session, ana, horta, enderezo="Lugar de Abaixo 3", localidade="Melide",
                     codigo_postal="15800", provincia="A Coruña", tipo_xip="AS",
                     asesoramento_nome="ATRIA Ulloa", asesoramento_fertilizacion=True)
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, enderezo="Rúa Nova 1",
                 localidade="Melide")
    crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1",
                  data_adquisicion=date(2020, 5, 1))
    return ana, horta


def test_primeira_folla_leva_enderezos_equipos_e_asesoramento(session):
    ana, horta = _escenario(session)
    libro = load_workbook(BytesIO(xerar_caderno(session, ana, horta.id, date(2026, 1, 1),
                                                date(2026, 12, 31))))
    filas = [[c for c in f if c not in (None, "")] for f in
             libro["1 Información xeral"].iter_rows(values_only=True)]
    assert ["Dirección", "Lugar de Abaixo 3"] in filas
    assert ["Dirección", "Rúa Nova 1"] in filas
    assert [1, "Mochila", "M1", "01/05/2020"] in filas
    assert ["ATRIA Ulloa", "AS"] in filas
    fert = [list(f) for f in libro["7 Fertilización"].iter_rows(values_only=True)]
    assert any(f[:2] == ["Asesoramento", "SI"] for f in fert)


def test_tipo_xip_descoñecido(session):
    ana, horta = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="XIP"):
        actualizar_horta(session, ana, horta, tipo_xip="XX")
