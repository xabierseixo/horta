"""Probas das funcións puras de texto e configuración da pantalla de visitas (tarefa 179b)."""

from __future__ import annotations

from datetime import date, time

from horta.ui.layout import SECCIONS
from horta.ui.pages.visitas import (
    COLUMNAS_TABOA,
    texto_aviso_proxima_visita,
    texto_cultivos_visitados,
    texto_hora_visita,
    texto_proxima_visita,
    texto_resumo_contos,
)


def test_texto_proxima_visita() -> None:
    assert texto_proxima_visita(date(2026, 7, 20)) == "20/07/2026"
    assert texto_proxima_visita(None) == "—"


def test_texto_aviso_proxima_visita() -> None:
    assert texto_aviso_proxima_visita(date(2026, 7, 20)) == "Visita do técnico o 20/07"
    assert texto_aviso_proxima_visita(date(2026, 3, 5)) == "Visita do técnico o 05/03"


def test_texto_cultivos_visitados() -> None:
    assert texto_cultivos_visitados(["Tomate", "Pemento"]) == "Tomate, Pemento"
    assert texto_cultivos_visitados([]) == "—"
    assert texto_cultivos_visitados(["", " "]) == "—"


def test_texto_hora_visita() -> None:
    assert texto_hora_visita(time(11, 45)) == "11:45"
    assert texto_hora_visita(time(8, 5)) == "08:05"
    assert texto_hora_visita(None) == ""


def test_texto_resumo_contos() -> None:
    assert texto_resumo_contos(1, 1) == "1 observación · 1 recomendación"
    assert texto_resumo_contos(3, 2) == "3 observacións · 2 recomendacións"
    assert texto_resumo_contos(0, 0) == "0 observacións · 0 recomendacións"


def test_columnas_taboa_visitas() -> None:
    campos = [col["field"] for col in COLUMNAS_TABOA]
    assert campos == [
        "data",
        "asesor",
        "cultivos",
        "num_observacions",
        "num_recomendacions",
        "proxima_visita",
    ]


def test_seccion_visitas_rexistrada() -> None:
    seccions_dict = {s.clave: s for s in SECCIONS}
    assert "visitas" in seccions_dict
    sec = seccions_dict["visitas"]
    assert sec.etiqueta == "Visitas do técnico"
    assert sec.icona == "person_pin_circle"
    assert sec.no_menu is True
