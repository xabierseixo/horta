"""Probas da memoria completa do plan de empresa (tarefa 184a)."""

from io import BytesIO

import pytest
from openpyxl import load_workbook

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.plan_empresa import (
    actualizar_plan,
    crear_plan,
    engadir_actividade,
    engadir_obxectivo,
    faltas_memoria,
    puntos,
    quitar,
    xerar_memoria,
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


def test_puntos_limpa_vinetas_e_linhas_baleiras():
    texto = """
    - Primeiro punto
    * Segundo punto
    • Terceiro punto

       -  Cuarto punto con espazos
    """
    assert puntos(texto) == [
        "Primeiro punto",
        "Segundo punto",
        "Terceiro punto",
        "Cuarto punto con espazos",
    ]
    assert puntos(None) == []
    assert puntos("   \n\n  ") == []
    assert puntos("- pay-back mantén guións internos") == ["pay-back mantén guións internos"]


def test_gardar_campos_novos(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan Memoria", 2027)
    actualizar_plan(
        session,
        ana,
        plan,
        dafo_debilidades="- Pouca terra\n- Falta maquinaria",
        dafo_ameazas="Secas e clima",
        dafo_fortalezas="Experiencia",
        dafo_oportunidades="Demanda ecolóxica",
        clientela="Consumidores directos",
        competencia="Outras hortas da comarca",
        mk_produto="Verdura fresca de tempada",
        mk_prezo="Prezos xustos",
        mk_canles="Grupos de consumo",
        mk_comunicacion="Redes e boca a boca",
        argumentos="Produto local e sen químicos",
        organizacion="Dúas persoas socias",
        riscos="Pragas e enfermidades",
        permisos="Rexistro de explotacións",
    )
    assert plan.dafo_debilidades == "- Pouca terra\n- Falta maquinaria"
    assert plan.clientela == "Consumidores directos"
    assert plan.riscos == "Pragas e enfermidades"
    assert plan.permisos == "Rexistro de explotacións"


def test_actividade_meses_mal_e_baleira_dan_erro_ben_gardase(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    # Mes inicio 0
    with pytest.raises(OperacionNonPermitidaError, match="meses"):
        engadir_actividade(session, ana, plan, 0, 5, "Sementeira")
    # Mes fin 13
    with pytest.raises(OperacionNonPermitidaError, match="meses"):
        engadir_actividade(session, ana, plan, 1, 13, "Sementeira")
    # Mes inicio 13
    with pytest.raises(OperacionNonPermitidaError, match="meses"):
        engadir_actividade(session, ana, plan, 13, 14, "Sementeira")
    # Fin antes de inicio
    with pytest.raises(OperacionNonPermitidaError, match="meses"):
        engadir_actividade(session, ana, plan, 6, 3, "Sementeira")
    # Actividade baleira
    with pytest.raises(OperacionNonPermitidaError):
        engadir_actividade(session, ana, plan, 1, 3, "   ")
    # Ben, gárdase
    act = engadir_actividade(session, ana, plan, 2, 4, "Preparar o solo", responsable="Xan")
    assert act.id is not None
    assert act.mes_inicio == 2
    assert act.mes_fin == 4
    assert act.actividade == "Preparar o solo"
    assert act.responsable == "Xan"
    assert len(plan.actividades) == 1


def test_obxectivo_sen_indicador_da_erro(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    with pytest.raises(OperacionNonPermitidaError, match="mide"):
        engadir_obxectivo(session, ana, plan, "Facturación", "")
    with pytest.raises(OperacionNonPermitidaError, match="mide"):
        engadir_obxectivo(session, ana, plan, "", "Euros")
    obx = engadir_obxectivo(
        session,
        ana,
        plan,
        "Aumentar produción",
        "kg colleitados",
        meta="1000 kg",
        prazo="6 meses",
    )
    assert obx.id is not None
    assert obx.obxectivo == "Aumentar produción"
    assert obx.indicador == "kg colleitados"
    assert obx.meta == "1000 kg"
    assert obx.prazo == "6 meses"
    assert len(plan.obxectivos) == 1


def test_quitar_actividade_doutro_plan_da_erro(session):
    ana, horta = _escenario(session)
    plan1 = crear_plan(session, ana, horta.id, "Plan 1", 2027)
    plan2 = crear_plan(session, ana, horta.id, "Plan 2", 2027)
    act1 = engadir_actividade(session, ana, plan1, 1, 3, "Actividade 1")
    with pytest.raises(OperacionNonPermitidaError, match="deste plan"):
        quitar(session, ana, plan2, act1)
    # Quitar do mesmo plan funciona
    quitar(session, ana, plan1, act1)
    assert len(plan1.actividades) == 0

    # Tamén con obxectivos
    obx1 = engadir_obxectivo(session, ana, plan1, "Obx 1", "Ind 1")
    with pytest.raises(OperacionNonPermitidaError, match="deste plan"):
        quitar(session, ana, plan2, obx1)
    quitar(session, ana, plan1, obx1)
    assert len(plan1.obxectivos) == 0


def test_faltas_memoria_plan_novo_e_cheo(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
    faltas = faltas_memoria(plan)
    assert len(faltas) == 7
    assert faltas == [
        "Punto de partida e organización",
        "DAFO",
        "Mercado",
        "Márketing",
        "Riscos e permisos",
        "Calendario de 12 meses",
        "Obxectivos e indicadores",
    ]
    # Enchemos polo menos un campo de cada sección e engadimos actividade e obxectivo
    actualizar_plan(
        session,
        ana,
        plan,
        situacion_partida="Partimos de cero",
        dafo_fortalezas="Moitas ganas",
        mercado="Mercado local",
        mk_produto="Tomates",
        riscos="Seca",
    )
    engadir_actividade(session, ana, plan, 1, 2, "Plantar")
    engadir_obxectivo(session, ana, plan, "Obxectivo", "Indicador")
    assert faltas_memoria(plan) == []


def test_xerar_memoria_excel(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Horta Ecolóxica", 2027)
    actualizar_plan(
        session,
        ana,
        plan,
        dafo_fortalezas="Calidade\nProximidade",
        dafo_debilidades="Man de obra",
    )
    engadir_actividade(session, ana, plan, 3, 5, "Sementeira de primavera", responsable="Xan")

    excel_bytes = xerar_memoria(session, ana, plan.id)
    wb = load_workbook(BytesIO(excel_bytes))
    assert wb.sheetnames == [
        "Proxecto",
        "DAFO",
        "Mercado",
        "Márketing",
        "Calendario",
        "Obxectivos",
        "Riscos e permisos",
        "Cifras",
    ]

    # DAFO ten unha fila por punto
    ws_dafo = wb["DAFO"]
    filas_dafo = [tuple(f) for f in ws_dafo.iter_rows(min_row=5, values_only=True)]
    assert ("Debilidades", "Man de obra") in filas_dafo
    assert ("Fortalezas", "Calidade") in filas_dafo
    assert ("Fortalezas", "Proximidade") in filas_dafo
    assert ("Ameazas", "—") in filas_dafo
    assert ("Oportunidades", "—") in filas_dafo

    # Calendario ten «■» só nos meses da actividade (3, 4, 5)
    ws_cal = wb["Calendario"]
    filas_cal = [tuple(f) for f in ws_cal.iter_rows(min_row=5, values_only=True)]
    assert len(filas_cal) == 1
    act, resp, *meses = filas_cal[0]
    assert act == "Sementeira de primavera"
    assert resp == "Xan"
    assert len(meses) == 12
    for idx, m in enumerate(meses, start=1):
        if 3 <= idx <= 5:
            assert m == "■", f"Mes {idx} debería ter ■"
        else:
            assert m in ("", None), f"Mes {idx} non debería ter ■"


def test_lector_non_pode_engadir_actividades(session):
    ana, horta = _escenario(session)
    plan = crear_plan(session, ana, horta.id, "Plan", 2027)
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
        engadir_actividade(session, luis, plan, 1, 2, "Regar")
    with pytest.raises(PermisoDenegadoError):
        engadir_obxectivo(session, luis, plan, "Obx", "Ind")
