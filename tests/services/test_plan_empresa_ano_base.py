"""Y9: o primeiro ano, sen datos do ano pasado, o plan parte do ano en curso."""

from datetime import date

from horta.models.usuario import RolGlobal, Usuario
from horta.services.cartos import DatosApunte, crear_apunte
from horta.services.hortas import crear_horta
from horta.services.plan_empresa import ano_de_referencia, crear_plan

HOXE = date(2026, 10, 29)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def _seguro(session, ana, horta, dia, importe):
    crear_apunte(session, ana, horta.id, DatosApunte(
        tipo="gasto", categoria="seguro", concepto="Seguro", data=dia, importe=importe),
        hoxe=HOXE)


def test_sen_ano_pasado_parte_do_ano_en_curso(session):
    ana, horta = _escenario(session)
    _seguro(session, ana, horta, date(2026, 3, 1), 300)
    assert ano_de_referencia(session, ana, horta.id, HOXE) == 2026
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    assert plan.anos[0].custos_fixos == 300


def test_co_ano_pasado_parte_del(session):
    ana, horta = _escenario(session)
    _seguro(session, ana, horta, date(2025, 3, 1), 500)
    _seguro(session, ana, horta, date(2026, 3, 1), 300)
    assert ano_de_referencia(session, ana, horta.id, HOXE) == 2025
    assert crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE).anos[0].custos_fixos \
        == 500
