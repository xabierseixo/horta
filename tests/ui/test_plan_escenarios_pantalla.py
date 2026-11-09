"""Textos da pantalla de escenarios, semáforo e media galega do plan de empresa."""

from __future__ import annotations

from horta.services.plan_empresa import Comparacion, pct
from horta.ui.pages.plan_empresa import (
    cor_do_sinal,
    nota_comparacion,
    texto_comparacion,
    texto_payback,
    texto_tir,
)


def test_cor_do_sinal() -> None:
    assert cor_do_sinal("verde") == "positive"
    assert cor_do_sinal("amarelo") == "warning"
    assert cor_do_sinal("vermello") == "negative"
    assert cor_do_sinal("outra") == "grey"


def test_porcentaxes_con_coma() -> None:
    assert pct(0.123) == "12,3 %"
    assert pct(0.05, 2) == "5,00 %"
    assert texto_tir(0.0826) == "8,3 %"
    assert texto_tir(None) == "—"
    assert texto_payback(3) == "3 anos"
    assert texto_payback(1) == "1 ano"
    assert texto_payback(None) == "—"


def test_texto_comparacion() -> None:
    c = Comparacion("Produción por hectárea", 30500.0, 26074.0, "€/ha", None)
    assert texto_comparacion(c) == (
        "Produción por hectárea: o teu plan 30 500 €/ha · media galega 26 074 €/ha"
    )
    custos = Comparacion("Custos sobre a produción", 61.25, None, "%", None)
    assert texto_comparacion(custos) == (
        "Custos sobre a produción: o teu plan 61,2 % · media galega —"
    )


def test_nota_comparacion() -> None:
    sen_superficie = Comparacion("Produción por hectárea", None, 26074.0, "€/ha", None)
    assert nota_comparacion(sen_superficie) == "Pon a superficie das parcelas para comparar"
    sen_uta = Comparacion("Produción por UTA", None, 24335.0, "€/UTA", None)
    assert nota_comparacion(sen_uta) == "Pon as UTA mantidas ou creadas (Datos) para comparar"
    con_nota = Comparacion("Resultado por UTA", 9000.0, 9287.0, "€/UTA", "Nota")
    assert nota_comparacion(con_nota) == "Nota"
