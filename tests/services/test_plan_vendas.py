"""Probas de vendas en detalle e tesouraría no plan de empresa (tarefa 185a)."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.lote import Lote, LoteSaida, ProdutoVenda
from horta.models.plan_empresa import PlanVenda
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.plan_empresa import (
    avisos_plan,
    conta,
    crear_plan,
    engadir_financiamento,
    engadir_investimento,
    engadir_venda,
    gardar_anos,
    marxes_por_venda,
    meses_de,
    propor_vendas_do_real,
    quitar,
    tesouraria,
    vendas_do_ano,
)


def _escenario(session):
    ana = Usuario(
        nome="ana",
        email="ana@example.com",
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(ana)
    session.commit()
    return ana, crear_horta(session, ana, "Horta")


def test_meses_de():
    assert meses_de("3, 1,3,13") == [1, 3]
    assert meses_de("") == list(range(1, 13))
    assert meses_de(" 12, 5, 5, 0, 15 ") == [5, 12]


def test_validacions_engadir_venda(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)

    # Produto ou unidade baleiros
    with pytest.raises(OperacionNonPermitidaError, match="produto e a unidade"):
        engadir_venda(session, ana, plan, "", "kg", "explotacion", 100, 2.5)
    with pytest.raises(OperacionNonPermitidaError, match="produto e a unidade"):
        engadir_venda(session, ana, plan, "Tomate", "  ", "explotacion", 100, 2.5)

    # Canle fóra de CANLES
    with pytest.raises(OperacionNonPermitidaError, match="canle"):
        engadir_venda(session, ana, plan, "Tomate", "kg", "inventada", 100, 2.5)

    # Cantidade ou prezo <= 0
    with pytest.raises(OperacionNonPermitidaError, match="maiores que 0"):
        engadir_venda(session, ana, plan, "Tomate", "kg", "explotacion", 0, 2.5)
    with pytest.raises(OperacionNonPermitidaError, match="maiores que 0"):
        engadir_venda(session, ana, plan, "Tomate", "kg", "explotacion", 100, 0)
    with pytest.raises(OperacionNonPermitidaError, match="maiores que 0"):
        engadir_venda(session, ana, plan, "Tomate", "kg", "explotacion", -5, 2.5)

    # Custo negativo
    with pytest.raises(OperacionNonPermitidaError, match="custo"):
        engadir_venda(
            session, ana, plan, "Tomate", "kg", "explotacion", 100, 2.5, custo_unitario=-1
        )

    # Crecementos por baixo de -100
    with pytest.raises(OperacionNonPermitidaError, match="crecemento"):
        engadir_venda(
            session,
            ana,
            plan,
            "Tomate",
            "kg",
            "explotacion",
            100,
            2.5,
            crece_cantidade_pct=-101,
        )
    with pytest.raises(OperacionNonPermitidaError, match="crecemento"):
        engadir_venda(
            session,
            ana,
            plan,
            "Tomate",
            "kg",
            "explotacion",
            100,
            2.5,
            crece_prezo_pct=-105,
        )

    # Venda correcta con meses
    venda = engadir_venda(
        session,
        ana,
        plan,
        "Tomate",
        "kg",
        "explotacion",
        100,
        2.5,
        custo_unitario=1.0,
        crece_cantidade_pct=5,
        crece_prezo_pct=2,
        meses=[6, 7, 8],
    )
    assert venda.id is not None
    assert venda.meses == "6,7,8"
    assert venda in plan.vendas_detalle

    # Quitar venda
    quitar(session, ana, plan, venda)
    assert venda not in plan.vendas_detalle


def test_vendas_do_ano_crecemento():
    venda = PlanVenda(
        plan_id=1,
        produto="Leituga",
        unidade="unidades",
        canle="mercado",
        cantidade=1000,
        prezo=2.0,
        custo_unitario=0.5,
        crece_cantidade_pct=10.0,
        crece_prezo_pct=5.0,
        meses="1,2,3,4,5,6,7,8,9,10,11,12",
    )
    # Ano 1: 1000 * 2.0 = 2000.0 de importe; custo = 1000 * 0.5 = 500.0
    imp1, cus1 = vendas_do_ano(venda, 1)
    assert imp1 == 2000.0
    assert cus1 == 500.0

    # Ano 3: cantidade = 1000 * 1.10^2 = 1210.0; prezo = 2.0 * 1.05^2 = 2.205
    # importe = 1210 * 2.205 = 2668.05; custo = 1210 * 0.5 = 605.0 (custo unitario non crece)
    imp3, cus3 = vendas_do_ano(venda, 3)
    assert imp3 == 2668.05
    assert cus3 == 605.0

    # Venda sen custo unitario: custo devolve 0.0
    venda_sen_custo = PlanVenda(
        plan_id=1,
        produto="Mazá",
        unidade="kg",
        canle="tenda",
        cantidade=500,
        prezo=1.5,
        custo_unitario=None,
    )
    assert vendas_do_ano(venda_sen_custo, 1) == (750.0, 0.0)


def test_conta_con_detalle_vendas_e_custos(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    gardar_anos(session, ana, plan, {n: (5000, 2000, 1000, 0) for n in range(1, 6)})

    # Sen vendas detalle, conta usa os valores de PlanAno
    c0 = conta(plan)[0]
    assert c0.vendas == 5000
    assert c0.variables == 2000

    # Engadimos venda sen custo_unitario
    engadir_venda(session, ana, plan, "Pemento", "kg", "tenda", 1000, 3.0)
    c1 = conta(plan)[0]
    # A sae das vendas: 1000 * 3 = 3000
    assert c1.vendas == 3000
    # B non cambia se ningunha venda ten custo_unitario: segue sendo o de PlanAno (2000)
    assert c1.variables == 2000

    # Engadimos venda con custo_unitario
    engadir_venda(
        session, ana, plan, "Cenoria", "kg", "mercado", 500, 2.0, custo_unitario=0.8
    )
    c2 = conta(plan)[0]
    # A = 3000 + 1000 = 4000
    assert c2.vendas == 4000
    # B sae das vendas: 500 * 0.8 = 400
    assert c2.variables == 400


def test_gardar_anos_non_pisa_vendas_cando_hai_detalle(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    engadir_venda(session, ana, plan, "Pemento", "kg", "tenda", 1000, 3.0)

    # Con detalle sen custo unitario: non cambia as vendas, pero si variables
    gardar_anos(session, ana, plan, {1: (99999, 1500, 800, 10)})
    ano1 = next(a for a in plan.anos if a.ano_n == 1)
    assert ano1.vendas == 0
    assert ano1.custos_variables == 1500
    assert ano1.custos_fixos == 800
    assert ano1.ingresos_financeiros == 10

    # Engadimos venda con custo unitario: agora tampouco cambia custos_variables
    engadir_venda(
        session, ana, plan, "Tomate", "kg", "explotacion", 500, 2.0, custo_unitario=0.5
    )
    gardar_anos(session, ana, plan, {1: (88888, 33333, 900, 20)})
    ano1 = next(a for a in plan.anos if a.ano_n == 1)
    assert ano1.vendas == 0
    assert ano1.custos_variables == 1500
    assert ano1.custos_fixos == 900
    assert ano1.ingresos_financeiros == 20


def test_marxes_por_venda_ordenadas(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    engadir_venda(
        session, ana, plan, "Framboesa", "kg", "tenda", 100, 10.0, custo_unitario=2.0
    )
    engadir_venda(
        session, ana, plan, "Pataca", "kg", "almacen", 3000, 1.0, custo_unitario=0.33
    )
    engadir_venda(session, ana, plan, "Herbas", "kg", "mercado", 50, 10.0)

    marxes = marxes_por_venda(plan)
    assert len(marxes) == 3
    # De maior a menor marxe: Pataca 2010 (3000 − 990) > Framboesa 800 > Herbas 500
    assert [m.produto for m in marxes] == ["Pataca", "Framboesa", "Herbas"]
    assert marxes[0].canle == "A un almacén ou cooperativa"
    assert marxes[0].marxe == 2010.0
    assert marxes[1].marxe == 800.0
    assert marxes[1].marxe_pct == 80.0
    assert marxes[2].marxe == 500.0
    assert marxes[2].marxe_pct == 100.0


def test_propor_vendas_do_real(session):
    ana, horta = _escenario(session)
    pv = ProdutoVenda(horta_id=horta.id, nome="Hortaliza", unidade="kg")
    session.add(pv)
    session.flush()
    lote1 = Lote(horta_id=horta.id, codigo="L01", produto="Xudía", unidade="kg",
                 produto_venda_id=pv.id, data=date(2025, 6, 1))
    lote2 = Lote(horta_id=horta.id, codigo="L02", produto="Tomate", unidade="kg",
                 produto_venda_id=pv.id, data=date(2025, 6, 1))
    session.add_all([lote1, lote2])
    session.flush()

    s1 = LoteSaida(
        horta_id=horta.id,
        lote_id=lote1.id,
        tipo="venda",
        cantidade=100,
        unidade="kg",
        importe=300.0,
        canle="mercado",
        data=date(2026, 5, 10),
        data_fin=date(2026, 5, 10),
        baixa=False,
    )
    s2 = LoteSaida(
        horta_id=horta.id,
        lote_id=lote1.id,
        tipo="venda",
        cantidade=200,
        unidade="kg",
        importe=600.0,
        canle="mercado",
        data=date(2026, 7, 15),
        data_fin=date(2026, 7, 15),
        baixa=False,
    )
    s3 = LoteSaida(
        horta_id=horta.id,
        lote_id=lote2.id,
        tipo="venda",
        cantidade=50,
        unidade="kg",
        importe=100.0,
        canle=None,
        data=date(2026, 8, 20),
        data_fin=date(2026, 8, 20),
        baixa=False,
    )
    session.add_all([s1, s2, s3])
    session.commit()

    plan = crear_plan(session, ana, horta.id, "Plan 2027", 2027)
    creadas = propor_vendas_do_real(session, ana, plan, 2026)
    assert creadas == 2
    assert len(plan.vendas_detalle) == 2

    v_xudia = next(v for v in plan.vendas_detalle if v.produto == "Xudía")
    assert v_xudia.cantidade == 300.0
    assert v_xudia.prezo == 3.0
    assert v_xudia.canle == "mercado"
    assert v_xudia.meses == "5,7"

    v_tomate = next(v for v in plan.vendas_detalle if v.produto == "Tomate")
    assert v_tomate.canle == "explotacion"
    assert v_tomate.meses == "8"

    # A segunda chamada dá erro porque xa ten detalle
    with pytest.raises(OperacionNonPermitidaError, match="xa ten vendas en detalle"):
        propor_vendas_do_real(session, ana, plan, 2026)


def test_tesouraria(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan 2027", 2027)

    # Investimento de 10 000 € con 21% IVE = 12 100 € no mes 1
    engadir_investimento(session, ana, plan, "3", "Tractor", 10000, iva_pct=21)

    # Financiamento: 5 000 € recursos propios (mes 1) e 5 000 € subvención (mes 12)
    engadir_financiamento(session, ana, plan, "propios", 5000)
    engadir_financiamento(session, ana, plan, "subvencion", 5000)

    # Venda só en xuño (mes 6): 6 000 €, custo_unitario=1 (1 000 €)
    engadir_venda(
        session,
        ana,
        plan,
        "Fresa",
        "kg",
        "tenda",
        1000,
        6.0,
        custo_unitario=1.0,
        meses=[6],
    )

    meses = tesouraria(plan)
    assert len(meses) == 12

    # Mes 1: cobro 5000 (fin propios), pago 12100 (investimento con IVE)
    assert meses[0].mes == 1
    assert meses[0].cobros == 5000.0
    assert meses[0].pagos == 12100.0
    assert meses[0].saldo == -7100.0

    # Meses 2 a 5: sen cobros nin pagos
    for m in range(2, 6):
        assert meses[m - 1].cobros == 0.0
        assert meses[m - 1].pagos == 0.0
        assert meses[m - 1].saldo == -7100.0

    # Mes 6 (xuño): cobro 6000 (venda só en xuño), pago 1000 (custo variable)
    assert meses[5].mes == 6
    assert meses[5].cobros == 6000.0
    assert meses[5].pagos == 1000.0
    assert meses[5].saldo == -2100.0

    # Mes 12: entra a subvención (5000 €)
    assert meses[11].mes == 12
    assert meses[11].cobros == 5000.0
    assert meses[11].saldo == 2900.0

    # O aviso de caixa negativa aparece en avisos_plan
    avisos = avisos_plan(plan)
    assert any(
        "No mes 1 a caixa queda en -7 100,00 €: precisas polo menos 7 100,00 € máis para empezar"
        in a
        for a in avisos
    )


def test_permiso_lector_non_pode_engadir_vendas(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)

    lector = Usuario(
        nome="lector",
        email="lector@example.com",
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(lector)
    session.commit()
    engadir_membro(session, ana, horta.id, lector, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        engadir_venda(session, lector, plan, "Cenoria", "kg", "explotacion", 100, 1.5)
