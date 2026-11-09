"""Probas da pantalla de vendas en detalle e tesouraría no plan de empresa (tarefa 185b)."""

from __future__ import annotations

from horta.models.plan_empresa import PlanVenda
from horta.services.plan_empresa import MarxeVenda, MesTesouraria
from horta.ui.numeros import parsear_decimal
from horta.ui.pages.plan_empresa import (
    MESES_TESOURARIA,
    _ValorFixo,
    opcions_tesouraria,
    texto_marxe,
    texto_venda,
)


def test_opcions_tesouraria():
    meses = [
        MesTesouraria(mes=m, cobros=100.0 * m, pagos=60.0 * m, saldo=40.0 * m)
        for m in range(1, 13)
    ]
    opc = opcions_tesouraria(meses)

    assert opc["xAxis"]["type"] == "category"
    assert len(opc["xAxis"]["data"]) == 12
    assert opc["xAxis"]["data"] == MESES_TESOURARIA
    assert opc["xAxis"]["data"][0] == "Xan"
    assert opc["xAxis"]["data"][-1] == "Dec"

    series = opc["series"]
    assert len(series) == 3

    cobros = next(s for s in series if s["name"] == "Cobros")
    assert cobros["type"] == "bar"
    assert cobros["data"] == [100.0 * m for m in range(1, 13)]

    pagos = next(s for s in series if s["name"] == "Pagos")
    assert pagos["type"] == "bar"
    assert pagos["data"] == [60.0 * m for m in range(1, 13)]

    saldo = next(s for s in series if "saldo" in s["name"].lower())
    assert saldo["type"] == "line"
    assert saldo["data"] == [40.0 * m for m in range(1, 13)]


def test_texto_venda_basica():
    v = PlanVenda(
        produto="Tomate",
        unidade="kg",
        canle="explotacion",
        cantidade=100.0,
        prezo=2.5,
        custo_unitario=None,
        crece_cantidade_pct=0,
        crece_prezo_pct=0,
        meses="1,2,3,4,5,6,7,8,9,10,11,12",
    )
    assert texto_venda(v) == "Tomate · Na explotación: 100 kg a 2,5 € (ano 1: 250,00 €)"


def test_texto_venda_con_custo_e_meses():
    v = PlanVenda(
        produto="Fresa",
        unidade="kg",
        canle="mercado",
        cantidade=200.0,
        prezo=4.0,
        custo_unitario=1.5,
        crece_cantidade_pct=0,
        crece_prezo_pct=0,
        meses="6,7,8",
    )
    assert texto_venda(v) == (
        "Fresa · Nun mercado: 200 kg a 4 € (ano 1: 800,00 €) · custo 1,5 €/kg · meses 6, 7, 8"
    )


def test_texto_venda_con_crecemento():
    # Só crecemento de cantidade
    v1 = PlanVenda(
        produto="Mazá",
        unidade="kg",
        canle="tenda",
        cantidade=500.0,
        prezo=2.0,
        crece_cantidade_pct=5.0,
        crece_prezo_pct=0,
        meses="1,2,3,4,5,6,7,8,9,10,11,12",
    )
    assert texto_venda(v1) == (
        "Mazá · A unha tenda: 500 kg a 2 € (ano 1: 1 000,00 €) · crece 5 %/ano"
    )

    # Só crecemento de prezo
    v2 = PlanVenda(
        produto="Mazá",
        unidade="kg",
        canle="tenda",
        cantidade=500.0,
        prezo=2.0,
        crece_cantidade_pct=0,
        crece_prezo_pct=3.0,
        meses="1,2,3,4,5,6,7,8,9,10,11,12",
    )
    assert texto_venda(v2) == (
        "Mazá · A unha tenda: 500 kg a 2 € (ano 1: 1 000,00 €) · crece 3 %/ano"
    )

    # Ambos crecementos iguais
    v3 = PlanVenda(
        produto="Mazá",
        unidade="kg",
        canle="tenda",
        cantidade=500.0,
        prezo=2.0,
        crece_cantidade_pct=4.0,
        crece_prezo_pct=4.0,
        meses="1,2,3,4,5,6,7,8,9,10,11,12",
    )
    assert texto_venda(v3) == (
        "Mazá · A unha tenda: 500 kg a 2 € (ano 1: 1 000,00 €) · crece 4 %/ano"
    )

    # Ambos crecementos distintos
    v4 = PlanVenda(
        produto="Pemento",
        unidade="kg",
        canle="domicilio",
        cantidade=300.0,
        prezo=3.0,
        custo_unitario=0.8,
        crece_cantidade_pct=10.0,
        crece_prezo_pct=5.0,
        meses="7,8,9",
    )
    assert texto_venda(v4) == (
        "Pemento · A domicilio: 300 kg a 3 € (ano 1: 900,00 €) · custo 0,8 €/kg · "
        "crece 10 cantidade, 5 prezo %/ano · meses 7, 8, 9"
    )


def test_texto_marxe():
    m1 = MarxeVenda(
        produto="Tomate",
        canle="Na explotación",
        importe=2500.0,
        custo=1000.0,
        marxe=1500.0,
        marxe_pct=60.0,
    )
    assert texto_marxe(m1) == (
        "Tomate · Na explotación: vende 2 500,00 €, custa 1 000,00 €, deixa 1 500,00 € (60 %)"
    )

    m2 = MarxeVenda(
        produto="Cenoria",
        canle="A domicilio",
        importe=0.0,
        custo=0.0,
        marxe=0.0,
        marxe_pct=None,
    )
    assert texto_marxe(m2) == (
        "Cenoria · A domicilio: vende 0,00 €, custa 0,00 €, deixa 0,00 € (—)"
    )


def test_valor_fixo():
    vf = _ValorFixo(1234.5)
    assert vf.value == "1234.5"
    assert parsear_decimal(vf.value) == 1234.5
