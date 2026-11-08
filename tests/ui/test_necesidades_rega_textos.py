"""Probas para os textos das necesidades de rega (texto_necesidade)."""

from __future__ import annotations

import pytest

from horta.services.necesidades_rega import NecesidadeRega
from horta.ui.necesidades_rega import texto_necesidade


def test_texto_necesidade_ok_con_falta():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=21.0,
        choiva_efectiva_mm=8.0,
        rega_mm=5.0,
        falta_mm=8.0,
        kc_actual=0.6,
        aproximado=False,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Faltan uns 8 l/m² (gastou 21, choveu 8 útiles, regouse 5)"
    )


def test_texto_necesidade_ok_con_falta_decimais():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=21.5,
        choiva_efectiva_mm=7.2,
        rega_mm=4.0,
        falta_mm=10.3,
        kc_actual=0.6,
        aproximado=False,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Faltan uns 10,3 l/m² (gastou 21,5, choveu 7,2 útiles, regouse 4)"
    )


def test_texto_necesidade_ok_con_falta_aproximado():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=21.0,
        choiva_efectiva_mm=8.0,
        rega_mm=5.0,
        falta_mm=8.0,
        kc_actual=0.6,
        aproximado=True,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Faltan uns 8 l/m² (gastou 21, choveu 8 útiles, regouse 5) · cálculo aproximado"
    )


def test_texto_necesidade_ok_sen_falta():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=15.0,
        choiva_efectiva_mm=10.0,
        rega_mm=10.0,
        falta_mm=0.0,
        kc_actual=0.6,
        aproximado=False,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Non fai falta regar (gastou 15 l/m², choveu 10 útiles, regouse 10)"
    )


def test_texto_necesidade_ok_sen_falta_decimais():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=15.5,
        choiva_efectiva_mm=10.2,
        rega_mm=8.5,
        falta_mm=0.0,
        kc_actual=0.6,
        aproximado=False,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Non fai falta regar (gastou 15,5 l/m², choveu 10,2 útiles, regouse 8,5)"
    )


def test_texto_necesidade_ok_sen_falta_aproximado():
    n = NecesidadeRega(
        cultivo_id=1,
        estado="ok",
        etc_mm=15.0,
        choiva_efectiva_mm=10.0,
        rega_mm=10.0,
        falta_mm=0.0,
        kc_actual=0.6,
        aproximado=True,
        dias_con_datos=7,
    )
    assert (
        texto_necesidade(n)
        == "Non fai falta regar (gastou 15 l/m², choveu 10 útiles, regouse 10) · cálculo aproximado"
    )


@pytest.mark.parametrize("aproximado", [False, True])
def test_texto_necesidade_secano(aproximado: bool):
    n = NecesidadeRega(
        cultivo_id=1,
        estado="secano",
        etc_mm=0.0,
        choiva_efectiva_mm=0.0,
        rega_mm=0.0,
        falta_mm=0.0,
        kc_actual=None,
        aproximado=aproximado,
        dias_con_datos=0,
    )
    assert texto_necesidade(n) == "Cultivo de secano"


@pytest.mark.parametrize("aproximado", [False, True])
def test_texto_necesidade_sen_coeficiente(aproximado: bool):
    n = NecesidadeRega(
        cultivo_id=1,
        estado="sen_coeficiente",
        etc_mm=0.0,
        choiva_efectiva_mm=0.0,
        rega_mm=0.0,
        falta_mm=0.0,
        kc_actual=None,
        aproximado=aproximado,
        dias_con_datos=0,
    )
    assert texto_necesidade(n) == "Non hai coeficiente oficial para este cultivo"


@pytest.mark.parametrize("aproximado", [False, True])
def test_texto_necesidade_sen_estacion(aproximado: bool):
    n = NecesidadeRega(
        cultivo_id=1,
        estado="sen_estacion",
        etc_mm=0.0,
        choiva_efectiva_mm=0.0,
        rega_mm=0.0,
        falta_mm=0.0,
        kc_actual=None,
        aproximado=aproximado,
        dias_con_datos=0,
    )
    assert (
        texto_necesidade(n)
        == "A parcela non ten estación de MeteoGalicia: escóllea en Parcelas"
    )


@pytest.mark.parametrize("aproximado", [False, True])
def test_texto_necesidade_sen_data_inicio(aproximado: bool):
    n = NecesidadeRega(
        cultivo_id=1,
        estado="sen_data_inicio",
        etc_mm=0.0,
        choiva_efectiva_mm=0.0,
        rega_mm=0.0,
        falta_mm=0.0,
        kc_actual=None,
        aproximado=aproximado,
        dias_con_datos=0,
    )
    assert texto_necesidade(n) == "Falta a data de sementeira ou plantación"


@pytest.mark.parametrize("aproximado", [False, True])
def test_texto_necesidade_sen_datos(aproximado: bool):
    n = NecesidadeRega(
        cultivo_id=1,
        estado="sen_datos",
        etc_mm=0.0,
        choiva_efectiva_mm=0.0,
        rega_mm=0.0,
        falta_mm=0.0,
        kc_actual=None,
        aproximado=aproximado,
        dias_con_datos=0,
    )
    assert texto_necesidade(n) == "Aínda non hai datos do tempo destes días"
