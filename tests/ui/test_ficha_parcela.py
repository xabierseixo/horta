"""Probas para a ficha da parcela (datos do caderno)."""

from __future__ import annotations

from datetime import date

from horta.models.parcela import Parcela, SecanoRegadio
from horta.ui.ficha_parcela import datos_caderno


def test_datos_caderno_completo() -> None:
    """Unha parcela con todos os datos do caderno mostra etiquetas e valores."""
    parcela = Parcela(
        nome="A Leira Grande",
        sigpac_provincia="15",
        sigpac_concello="78",
        sigpac_agregado="0",
        sigpac_zona="0",
        sigpac_poligono="12",
        sigpac_parcela="7477",
        sigpac_subparcela="1",
        uso_aproveitamento="TA",
        superficie=1.5,
        secano_regadio=SecanoRegadio.REGADIO,
        rexime_tenencia="1",
        data_alta=date(2026, 4, 15),
        estado="activa",
    )
    nomes_tenencia = {"1": "Propiedade"}
    nomes_causa = {"01": "Venda"}
    datos = datos_caderno(parcela, nomes_tenencia, nomes_causa)

    esperados = [
        ("Provincia", "15"),
        ("Concello", "78"),
        ("Agregado", "0"),
        ("Zona", "0"),
        ("Polígono", "12"),
        ("Parcela", "7477"),
        ("Recinto", "1"),
        ("Uso SIXPAC", "TA"),
        ("Superficie SIXPAC", "1,50 ha"),
        ("Secano/Regadío", "Regadío"),
        ("Réxime de tenencia", "Propiedade"),
        ("Data de alta", "15/04/2026"),
    ]
    assert datos == esperados


def test_datos_caderno_sen_sigpac() -> None:
    """Unha parcela sen datos SIGPAC non inclúe esas liñas."""
    parcela = Parcela(
        nome="Horta da Casa",
        superficie=0.035,
        secano_regadio=SecanoRegadio.SECANO,
        data_alta=date(2026, 2, 1),
        estado="activa",
    )
    datos = datos_caderno(parcela, {}, {})
    etiquetas = [e for e, _ in datos]

    for campo in ["Provincia", "Concello", "Agregado", "Zona", "Polígono", "Parcela", "Recinto"]:
        assert campo not in etiquetas
    assert "Uso SIXPAC" not in etiquetas

    assert ("Superficie SIXPAC", "350 m²") in datos
    assert ("Secano/Regadío", "Secano") in datos
    assert ("Data de alta", "01/02/2026") in datos


def test_datos_caderno_de_baixa() -> None:
    """Unha parcela de baixa mostra a data e a causa co seu nome."""
    parcela = Parcela(
        nome="Leira Vella",
        superficie=0.8,
        data_alta=date(2025, 1, 1),
        estado="baixa",
        data_baixa=date(2026, 11, 4),
        causa_baixa="02",
    )
    nomes_causa = {"02": "Fin do arrendamento"}
    datos = datos_caderno(parcela, {}, nomes_causa)

    assert ("Data de alta", "01/01/2025") in datos
    assert ("Data de baixa", "04/11/2026") in datos
    assert ("Causa da baixa", "Fin do arrendamento") in datos
