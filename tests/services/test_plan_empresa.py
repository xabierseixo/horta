"""Plan de empresa (paso 16)."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.plan_empresa import PlanFinanciamento
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cartos import DatosApunte, crear_apunte
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.plan_empresa import (
    conta,
    crear_plan,
    engadir_financiamento,
    engadir_investimento,
    gardar_anos,
    indicadores,
    seguimento,
    xuros,
)

HOXE = date(2026, 10, 29)


def _escenario(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_proposta_desde_o_real_e_conta(session):
    ana, horta = _escenario(session)
    crear_apunte(session, ana, horta.id, DatosApunte(
        tipo="gasto", categoria="seguro", concepto="Seguro", data=date(2025, 3, 1),
        importe=500), hoxe=HOXE)
    plan = crear_plan(session, ana, horta.id, "Obradoiro", 2027, hoxe=HOXE)
    assert [(a.vendas, a.custos_variables, a.custos_fixos) for a in plan.anos] == [
        (0, 0, 500)] * 5
    gardar_anos(session, ana, plan, {n: (20000, 8000, 2000) for n in range(1, 6)})
    engadir_investimento(session, ana, plan, "3", "Cámara de frío", 10000, vida_util_anos=10,
                         ofertas=3)
    engadir_investimento(session, ana, plan, "1", "Terreo", 5000, iva_pct=0, ofertas=3)
    engadir_financiamento(session, ana, plan, "propios", 7100)
    engadir_financiamento(session, ana, plan, "prestamo", 10000, xuro_pct=0, anos=5)
    ano1 = conta(plan)[0]
    # D: só a cámara (o terreo non se amortiza); E = 20000 − (8000 + 2000 + 1000)
    assert (ano1.ano, ano1.amortizacions, ano1.marxe, ano1.financeiro, ano1.beneficio) == (
        2027, 1000, 9000, 0, 9000)
    ind = indicadores(plan)
    assert ind.investimento == 15000 and ind.investimento_con_iva == 17100
    assert ind.payback == 2 and ind.tir is not None and ind.van > 0


def test_xuros_do_prestamo():
    prestamo = PlanFinanciamento(tipo="prestamo", importe=10000, xuro_pct=5, anos=2)
    assert xuros(prestamo) == [500.0, 256.1]


def test_validacions_e_permisos(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="xuro"):
        engadir_financiamento(session, ana, plan, "prestamo", 1000)
    luis = Usuario(nome="luis", email="luis@example.com", password_hash="x",
                   rol=RolGlobal.USUARIO, activo=True)
    session.add(luis)
    session.commit()
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        seguimento(session, luis, plan)


def test_anexos_en_excel(session):
    from io import BytesIO

    from openpyxl import load_workbook

    from horta.services.plan_empresa import xerar_anexos

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    engadir_investimento(session, ana, plan, "3", "Tractor", 1000, ofertas=1)
    libro = load_workbook(BytesIO(xerar_anexos(session, ana, plan.id)))
    assert libro.sheetnames == ["Anexo III", "Conta 5 anos", "Anexo V"]
    assert libro["Anexo V"]["E5"].value == 1210
