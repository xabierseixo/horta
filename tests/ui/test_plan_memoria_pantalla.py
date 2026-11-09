"""Probas da pantalla do plan de empresa e da memoria complementaria (tarefa 184b)."""

from __future__ import annotations

from horta.models.plan_empresa import PlanActividade, PlanObxectivo
from horta.ui.pages.plan_empresa import seccion_plan_empresa, texto_actividade, texto_obxectivo


def test_importacion_pantalla_plan_empresa() -> None:
    assert callable(seccion_plan_empresa)
    assert callable(texto_actividade)
    assert callable(texto_obxectivo)


def test_texto_actividade_un_mes_sen_responsable() -> None:
    act = PlanActividade(mes_inicio=3, mes_fin=3, actividade="Sementeira de leitugas")
    assert texto_actividade(act) == "Mes 3: Sementeira de leitugas"


def test_texto_actividade_varios_meses_sen_responsable() -> None:
    act = PlanActividade(mes_inicio=1, mes_fin=4, actividade="Preparación da terra")
    assert texto_actividade(act) == "Mes 1–4: Preparación da terra"


def test_texto_actividade_un_mes_con_responsable() -> None:
    act = PlanActividade(
        mes_inicio=5,
        mes_fin=5,
        actividade="Rega por goteo",
        responsable="Xan",
    )
    assert texto_actividade(act) == "Mes 5: Rega por goteo · Xan"


def test_texto_actividade_varios_meses_con_responsable() -> None:
    act = PlanActividade(
        mes_inicio=6,
        mes_fin=9,
        actividade="Colleita e distribución",
        responsable="Ana",
    )
    assert texto_actividade(act) == "Mes 6–9: Colleita e distribución · Ana"


def test_texto_obxectivo_sen_meta_nin_prazo() -> None:
    obx = PlanObxectivo(obxectivo="Facturación directa", indicador="Facturación mensual")
    assert texto_obxectivo(obx) == "Facturación directa — mídese con Facturación mensual"


def test_texto_obxectivo_con_meta_sen_prazo() -> None:
    obx = PlanObxectivo(
        obxectivo="Facturación directa",
        indicador="Facturación mensual",
        meta="20 000 €",
    )
    assert (
        texto_obxectivo(obx)
        == "Facturación directa — mídese con Facturación mensual · meta: 20 000 €"
    )


def test_texto_obxectivo_sen_meta_con_prazo() -> None:
    obx = PlanObxectivo(
        obxectivo="Facturación directa",
        indicador="Facturación mensual",
        prazo="ano 2",
    )
    assert (
        texto_obxectivo(obx)
        == "Facturación directa — mídese con Facturación mensual · prazo: ano 2"
    )


def test_texto_obxectivo_con_meta_e_prazo() -> None:
    obx = PlanObxectivo(
        obxectivo="Facturación directa",
        indicador="Facturación mensual",
        meta="20 000 €",
        prazo="ano 2",
    )
    assert (
        texto_obxectivo(obx)
        == "Facturación directa — mídese con Facturación mensual · meta: 20 000 € · prazo: ano 2"
    )
