"""Instalacións e animais identificados (paso 14)."""

from datetime import date

import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.animais import (
    actualizar_animal,
    actualizar_identificado,
    aviso_identificados,
    crear_animal,
    crear_identificado,
    listar_identificados,
)
from horta.services.errors import OperacionNonPermitidaError
from horta.services.historial import por_referencia
from horta.services.hortas import crear_horta
from horta.services.instalacions import crear_instalacion, listar_instalacions


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    vacas = crear_animal(session, ana, horta.id, "Vacas", cantidade=2,
                         data_alta=date(2026, 1, 1))
    return ana, horta, vacas


def test_instalacion_e_animais_nela(session):
    ana, horta, vacas = _escenario(session)
    corte = crear_instalacion(session, ana, horta.id, "corte", "Corte de abaixo")
    actualizar_animal(session, ana, vacas, instalacion_id=corte.id)
    assert [i.nome for i in listar_instalacions(session, ana, horta.id)] == ["Corte de abaixo"]
    with pytest.raises(OperacionNonPermitidaError, match="tipo"):
        crear_instalacion(session, ana, horta.id, "castelo", "Torre")
    outra = crear_horta(session, ana, "Outra")
    alleo = crear_instalacion(session, ana, outra.id, "corte", "Allea")
    with pytest.raises(OperacionNonPermitidaError, match="non é desta"):
        actualizar_animal(session, ana, vacas, instalacion_id=alleo.id)
    assert por_referencia(session, "instalacion", corte.id)[0].que == "Grupo de animais"


def test_animais_identificados(session):
    ana, horta, vacas = _escenario(session)
    alta = date(2026, 1, 1)
    marela = crear_identificado(session, ana, vacas, identificador="ES0123", nome="Marela",
                                sexo="femia", data_alta=alta)
    assert aviso_identificados(session, vacas) == (
        "No grupo hai 2 animais e 1 identificados de alta")
    crear_identificado(session, ana, vacas, identificador="ES0124", data_alta=alta)
    assert aviso_identificados(session, vacas) is None
    with pytest.raises(OperacionNonPermitidaError, match="Xa hai"):
        crear_identificado(session, ana, vacas, identificador="ES0123", data_alta=alta)
    actualizar_identificado(session, ana, marela, identificador="ES0123", nome="Marela",
                            data_alta=alta, data_baixa=date(2026, 5, 1))
    assert [i.identificador for i in listar_identificados(session, ana, vacas)] == [
        "ES0124", "ES0123"]
