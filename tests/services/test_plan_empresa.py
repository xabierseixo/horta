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
    gardar_anos(session, ana, plan, {n: (20000, 8000, 2000, 0) for n in range(1, 6)})
    engadir_investimento(session, ana, plan, "3", "Cámara de frío", 10000, vida_util_anos=10)
    engadir_investimento(session, ana, plan, "1", "Terreo", 5000, iva_pct=0)
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
    engadir_investimento(session, ana, plan, "3", "Tractor", 1000)
    engadir_investimento(session, ana, plan, "4", "Proxecto técnico", 500)
    libro = load_workbook(BytesIO(xerar_anexos(session, ana, plan.id)))
    assert libro.sheetnames == ["Anexo III", "Conta 5 anos", "Anexo V", "Anexo VI-A",
                                "Anexo VI-B", "Documentación", "Localización"]
    filas = [tuple(f) for f in libro["Anexo V"].iter_rows(min_row=5, values_only=True)]
    assert ("3. Maquinaria e equipamento", "Tractor", 1000, 21, 1210) in filas
    assert ("4. Estudos, proxectos e honorarios", "Proxecto técnico", 500, 21, 605) in filas
    assert filas[-1] == ("TOTAL PARTIDAS", None, 1500, None, 1815)


def _provedores(session, ana, horta):
    from horta.services.persoas import crear_persoa

    return [crear_persoa(session, ana, horta.id, nome, papeis={"provedor"}, nif=nif)
            for nome, nif in (("Frío SL", "12345678Z"), ("Xeo SA", None),
                              ("Polar", "11111111H"))]


def test_ofertas_do_anexo_vi_a(session):
    from horta.services.plan_empresa import avisos_ofertas, engadir_oferta

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    camara = engadir_investimento(session, ana, plan, "3", "Cámara", 10000)
    assert "hai 0 ofertas" in avisos_ofertas(camara)[0]
    a, b, c = _provedores(session, ana, horta)
    engadir_oferta(session, ana, plan, camara, a.id, 10000, elixida=True, criterio="Prazo")
    engadir_oferta(session, ana, plan, camara, b.id, 9500)
    with pytest.raises(OperacionNonPermitidaError, match="xa ten"):
        engadir_oferta(session, ana, plan, camara, a.id, 9000)
    avisos = avisos_ofertas(camara)
    assert any("hai 2 ofertas" in x for x in avisos)
    assert any("non é a máis económica" in x for x in avisos)
    # Elixir outra deixa só unha elixida
    engadir_oferta(session, ana, plan, camara, c.id, 9000, elixida=True)
    assert {o.provedor_id for o in camara.ofertas if o.elixida} == {c.id}
    assert avisos_ofertas(camara) == [
        "«Cámara»: o importe (10 000,00 €) non é o da oferta elixida (9 000,00 €)"]


def test_motivo_sen_tres_ofertas(session):
    from horta.services.plan_empresa import avisos_ofertas

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    unica = engadir_investimento(session, ana, plan, "3", "Muíño", 4000,
                                 motivo_sen_ofertas="Só o fabrica unha empresa")
    assert avisos_ofertas(unica) == []


def test_iva_non_recuperable_e_ingresos_financeiros(session):
    from horta.services.plan_empresa import actualizar_plan

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    engadir_investimento(session, ana, plan, "3", "Cámara", 10000, vida_util_anos=10)
    gardar_anos(session, ana, plan, {1: (0, 0, 0, 50)})
    assert indicadores(plan).subvencionable == 10000
    assert conta(plan)[0].financeiro == 50
    actualizar_plan(session, ana, plan, iva_recuperable=False)
    assert indicadores(plan).subvencionable == 12100
    assert conta(plan)[0].amortizacions == 1210


def test_tipoloxia_e_pequena_empresa(session):
    from horta.services.plan_empresa import actualizar_plan, avisos_plan

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    with pytest.raises(OperacionNonPermitidaError, match="tipoloxía"):
        actualizar_plan(session, ana, plan, tipoloxia="outra")
    actualizar_plan(session, ana, plan, tipoloxia="primaria_complementaria",
                    traballadores=50, facturacion=11e6, balance=12e6)
    engadir_investimento(session, ana, plan, "3", "Tractor", 31000,
                         motivo_sen_ofertas="Proba")
    avisos = avisos_plan(plan)
    assert any("pasa do máximo de 30 000,00 €" in x for x in avisos)
    assert any("50 persoas" in x for x in avisos)
    assert any("10 millóns" in x for x in avisos)


def test_faltas_e_documentacion(session):
    from horta.services.persoas import crear_persoa
    from horta.services.plan_empresa import (
        actualizar_plan,
        documentos_plan,
        engadir_oferta,
        faltas_plan,
    )

    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)
    faltas = faltas_plan(session, ana, plan)
    assert "o NIF do titular (en Persoas)" in faltas
    assert "o investimento (Anexo V)" in faltas
    crear_persoa(session, ana, horta.id, "Ana", papeis={"titular"}, nif="00000000T")
    actualizar_plan(session, ana, plan, tipoloxia="primaria_enerxia", cnae="0113",
                    descricion="d", proceso="p", formacion="f", situacion_partida="s",
                    metodoloxia="m", empresa_nova=True, uta_creadas=1,
                    ofertas_autenticas=True, sen_vinculo_promotor=True,
                    sen_vinculo_entre_provedores=True)
    gardar_anos(session, ana, plan, {1: (1000, 0, 0, 0)})
    obra = engadir_investimento(session, ana, plan, "2", "Placas", 3000)
    engadir_financiamento(session, ana, plan, "propios", 3630)
    _, sen_nif, _ = _provedores(session, ana, horta)
    engadir_oferta(session, ana, plan, obra, sen_nif.id, 3000, elixida=True)
    assert faltas_plan(session, ana, plan) == ["o NIF de Xeo SA (en Contactos)"]
    docs = {d.letra: d for d in documentos_plan(session, ana, plan)}
    assert "c" not in docs and "l" not in docs  # empresa nova
    assert "m" in docs and "n" not in docs  # obra civil, sen maquinaria
    assert not docs["j"].da_app  # sen código de explotación na ficha
    assert docs["f"].da_app and docs["k"].da_app
