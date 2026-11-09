"""Probas de escenarios, semáforo, revisión e comparación RECAN no plan de empresa (tarefa 186a)."""

from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.lote import Lote, LoteSaida, ProdutoVenda
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.parcelas import crear_parcela
from horta.services.plan_empresa import (
    actualizar_plan,
    comparar_recan,
    conta,
    crear_plan,
    engadir_financiamento,
    engadir_investimento,
    escenarios,
    fonte_recan,
    gardar_anos,
    orientacions_recan,
    revision,
    semaforo,
)

HOXE = date(2026, 10, 29)


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


def test_escenarios(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Fruteiras", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan, {n: (20000, 5000, 2000, 0) for n in range(1, 6)})
    engadir_investimento(session, ana, plan, "3", "Tractor", 10000, vida_util_anos=5)
    engadir_financiamento(session, ana, plan, "propios", 12100)
    actualizar_plan(session, ana, plan, escenario_pct=25)

    esc = escenarios(plan)
    assert len(esc) == 3
    pes, nor, opt = esc

    assert pes.nome == "Pesimista" and pes.factor == 0.75
    assert nor.nome == "Normal" and nor.factor == 1.0
    assert opt.nome == "Optimista" and opt.factor == 1.25

    assert pes.vendas_ano1 == 15000.0
    assert nor.vendas_ano1 == 20000.0
    assert opt.vendas_ano1 == 25000.0

    assert pes.beneficio_ano1 < nor.beneficio_ano1 < opt.beneficio_ano1
    assert pes.van < nor.van < opt.van


def test_conta_factor_vendas(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Base", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan, {n: (10000, 3000, 1500, 200) for n in range(1, 6)})
    engadir_investimento(session, ana, plan, "3", "Apero", 4000, vida_util_anos=4)

    filas_1 = conta(plan, 1.0)
    filas_08 = conta(plan, 0.8)

    assert len(filas_08) == 5
    ano1_base, ano1_08 = filas_1[0], filas_08[0]

    assert ano1_08.vendas == 8000.0
    assert ano1_08.variables == ano1_base.variables == 3000.0
    assert ano1_08.fixos == ano1_base.fixos == 1500.0
    assert ano1_08.amortizacions == ano1_base.amortizacions == 1000.0
    assert ano1_08.financeiro == ano1_base.financeiro == 200.0
    assert ano1_08.marxe == round(8000.0 - (3000.0 + 1500.0 + 1000.0), 2)


def test_semaforo(session):
    ana, horta = _escenario(session)

    # 1. Plan bo
    plan_bo = crear_plan(session, ana, horta.id, "Plan Bo", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan_bo, {n: (30000, 6000, 2000, 0) for n in range(1, 6)})
    engadir_investimento(session, ana, plan_bo, "3", "Cámara", 5000, vida_util_anos=5)
    engadir_financiamento(session, ana, plan_bo, "propios", 6050)

    sinais_bo = semaforo(plan_bo)
    assert len(sinais_bo) == 5
    assert [s.nome for s in sinais_bo] == [
        "VAN",
        "TIR",
        "Pay-back",
        "Caixa do ano 1",
        "Escenario pesimista",
    ]
    sinal_van = next(s for s in sinais_bo if s.nome == "VAN")
    assert sinal_van.cor == "verde"
    assert sinal_van.texto == "O proxecto recupera o investimento e a taxa pedida"

    # 2. Plan malo con vendas 0
    plan_malo = crear_plan(session, ana, horta.id, "Plan Malo", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan_malo, {n: (0, 0, 1000, 0) for n in range(1, 6)})
    engadir_investimento(session, ana, plan_malo, "3", "Nave", 20000, vida_util_anos=10)
    engadir_financiamento(session, ana, plan_malo, "propios", 24200)

    sinais_malo = semaforo(plan_malo)
    sinal_van_m = next(s for s in sinais_malo if s.nome == "VAN")
    assert sinal_van_m.cor == "vermello"
    sinal_pb_m = next(s for s in sinais_malo if s.nome == "Pay-back")
    assert sinal_pb_m.cor == "vermello"


def test_revision(session):
    ana, horta = _escenario(session)

    # Venda real no ano anterior (2025): as vendas de Contas saen das saídas dos lotes
    pv = ProdutoVenda(horta_id=horta.id, nome="Leituga", unidade="kg")
    session.add(pv)
    session.flush()
    lote = Lote(horta_id=horta.id, codigo="L01", produto="Leituga", unidade="kg",
                produto_venda_id=pv.id, data=date(2025, 5, 1))
    session.add(lote)
    session.flush()
    session.add(LoteSaida(horta_id=horta.id, lote_id=lote.id, tipo="venda", cantidade=1000,
                          unidade="kg", canle="mercado", importe=2000,
                          data=date(2025, 5, 10), data_fin=date(2025, 5, 10)))
    session.commit()

    # Plan con vendas moi por riba do real (10 000 fronte a 2 000) e sen ofertas
    plan = crear_plan(session, ana, horta.id, "Plan Expansión", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan, {n: (10000, 2000, 1000, 0) for n in range(1, 6)})
    engadir_investimento(session, ana, plan, "3", "Tractor", 8000)

    rev = revision(session, ana, plan)
    assert any("máis cás reais" in f for f in rev.falta_probar)
    assert any("Faltan ofertas en: Tractor" in f for f in rev.falta_probar)

    # Plan coas vendas axustadas ao real e investimento con motivo
    plan2 = crear_plan(session, ana, horta.id, "Plan Prudente", 2027, hoxe=HOXE)
    gardar_anos(session, ana, plan2, {n: (2100, 500, 200, 0) for n in range(1, 6)})
    engadir_investimento(
        session,
        ana,
        plan2,
        "3",
        "Apero",
        3000,
        motivo_sen_ofertas="Fabricante único en Galicia",
    )
    engadir_financiamento(session, ana, plan2, "propios", 3630)

    rev2 = revision(session, ana, plan2)
    assert any("están ao nivel das reais" in a for a in rev2.afirmable)
    assert any("Todos os gastos teñen tres ofertas ou o motivo" in a for a in rev2.afirmable)
    assert any("cadra co investimento con IVE" in a for a in rev2.afirmable)


def test_orientacions_recan():
    ot = orientacions_recan()
    assert len(ot) == 10
    assert set(ot.keys()) == {
        "Todas",
        "16",
        "20",
        "35",
        "36",
        "45",
        "48",
        "49",
        "50",
        "80",
    }
    assert ot["20"] == "Horticultura"
    assert fonte_recan().startswith("MAPA")


def test_comparar_recan(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Hortícola", 2027, hoxe=HOXE)

    # Sen ote_recan a comparación está baleira
    assert comparar_recan(session, ana, plan) == []

    # Con ote_recan "20", parcelas e UTA
    crear_parcela(session, ana, horta.id, "Horta Norte", superficie=2.0)
    actualizar_plan(session, ana, plan, ote_recan="20", uta_mantidas=1.5)
    gardar_anos(session, ana, plan, {n: (50000, 12000, 4000, 0) for n in range(1, 6)})

    comps = comparar_recan(session, ana, plan)
    assert len(comps) == 4

    # 1. Produción por hectárea
    c_ha = comps[0]
    assert c_ha.indicador == "Produción por hectárea"
    assert c_ha.unidade == "€/ha"
    assert c_ha.plan == round(50000 / 2.0)
    assert c_ha.media == 26074
    assert c_ha.nota is None

    # 2. Produción por UTA
    c_uta = comps[1]
    assert c_uta.indicador == "Produción por UTA"
    assert c_uta.unidade == "€/UTA"
    assert c_uta.plan == round(50000 / 1.5)
    assert c_uta.media == 24335
    assert c_uta.nota is None

    # 3. Custos sobre a produción
    c_custos = comps[2]
    assert c_custos.indicador == "Custos sobre a produción"
    assert c_custos.unidade == "%"
    assert c_custos.plan == round((12000 + 4000) / 50000 * 100, 1)
    assert c_custos.media == 61.9

    # 4. Resultado por UTA
    c_res = comps[3]
    assert c_res.indicador == "Resultado por UTA"
    assert c_res.unidade == "€/UTA"
    assert c_res.media == 9287
    assert c_res.nota == "A RECAN inclúe as subvencións correntes; o plan non"

    # Con orientación de poucas explotacións (mostra < 15)
    actualizar_plan(session, ana, plan, ote_recan="36")  # Froiteiras: mostra 14
    comps_pouca = comparar_recan(session, ana, plan)
    assert comps_pouca[0].nota == "Media con poucas explotacións na mostra (14)"


def test_actualizar_plan_validacions_escenarios_e_recan(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Validar", 2027, hoxe=HOXE)

    # escenario_pct fóra de 1..90
    with pytest.raises(
        OperacionNonPermitidaError, match="A variación dos escenarios vai do 1 ao 90 %"
    ):
        actualizar_plan(session, ana, plan, escenario_pct=0)
    with pytest.raises(
        OperacionNonPermitidaError, match="A variación dos escenarios vai do 1 ao 90 %"
    ):
        actualizar_plan(session, ana, plan, escenario_pct=95)

    # ote_recan non existente
    with pytest.raises(OperacionNonPermitidaError, match="Esa orientación da RECAN non existe"):
        actualizar_plan(session, ana, plan, ote_recan="999")

    # Valores correctos
    actualizar_plan(session, ana, plan, escenario_pct=15, ote_recan="20")
    assert plan.escenario_pct == 15
    assert plan.ote_recan == "20"

    actualizar_plan(session, ana, plan, ote_recan=None)
    assert plan.ote_recan is None


def test_revision_media_recan_uta_dobre(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Gran Produción", 2027, hoxe=HOXE)
    actualizar_plan(session, ana, plan, ote_recan="20", uta_mantidas=1.0)
    # Horticultura: media RECAN de produción por UTA é 24335 €/UTA
    # Cunha produción de 70 000 e 1 UTA dá 70 000 (> 2 * 24335 = 48670)
    gardar_anos(session, ana, plan, {n: (70000, 10000, 5000, 0) for n in range(1, 6)})

    rev = revision(session, ana, plan)
    msg_esperada = (
        "A produción por UTA prevista é 2,9 veces a media galega da RECAN: explica por que"
    )
    assert any(msg_esperada in f for f in rev.falta_probar)


def test_permisos_servizos(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027, hoxe=HOXE)

    luis = Usuario(
        nome="luis",
        email="luis@example.com",
        password_hash="x",
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(luis)
    session.commit()
    engadir_membro(session, ana, horta.id, luis, RolHorta.LECTOR)

    with pytest.raises(PermisoDenegadoError):
        revision(session, luis, plan)
    with pytest.raises(PermisoDenegadoError):
        comparar_recan(session, luis, plan)
    with pytest.raises(PermisoDenegadoError):
        actualizar_plan(session, luis, plan, escenario_pct=10)
