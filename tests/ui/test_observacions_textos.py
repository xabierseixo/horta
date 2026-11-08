"""Probas unitarias das funcións puras de textos de observacións de pragas."""

from __future__ import annotations

from types import SimpleNamespace

from horta.models.observacion import ObservacionPraga
from horta.ui.layout import SECCIONS
from horta.ui.pages.diario import _CONSTRUTORES, _MODELOS, ICONAS, SECCION_DO_TIPO
from horta.ui.pages.observacions import (
    dialogo_observacion,
    texto_conto_ou_nivel,
    texto_limiar,
    texto_supera,
)


def test_texto_conto_ou_nivel_con_conto_e_unidade() -> None:
    assert texto_conto_ou_nivel(5.0, "capturas por trampa") == "5 capturas por trampa"
    assert texto_conto_ou_nivel(12.5, "% de follas") == "12.5 % de follas"


def test_texto_conto_ou_nivel_so_conto() -> None:
    assert texto_conto_ou_nivel(3.0) == "3"


def test_texto_conto_ou_nivel_so_nivel() -> None:
    assert texto_conto_ou_nivel(None, nivel="baixo") == "Baixo"
    assert texto_conto_ou_nivel(None, nivel="medio") == "Medio"
    assert texto_conto_ou_nivel(None, nivel="alto") == "Alto"


def test_texto_conto_ou_nivel_conto_e_nivel() -> None:
    assert (
        texto_conto_ou_nivel(10.0, "capturas por trampa", "medio")
        == "10 capturas por trampa (Medio)"
    )


def test_texto_conto_ou_nivel_baleiro() -> None:
    assert texto_conto_ou_nivel(None, None, None) == ""


def test_texto_limiar_con_valor() -> None:
    assert texto_limiar(10.0) == "10"
    assert texto_limiar(3.5) == "3.5"


def test_texto_limiar_con_obxecto() -> None:
    limiar = SimpleNamespace(valor=8.0, unidade_conto="capturas por trampa")
    assert texto_limiar(limiar) == "8"


def test_texto_limiar_sen_limiar() -> None:
    assert texto_limiar(None) == "—"


def test_texto_supera() -> None:
    assert texto_supera(True) == "Si"
    assert texto_supera(False) == ""


def test_rexistro_seccion_e_diario() -> None:
    seccions_claves = {s.clave: s for s in SECCIONS}
    assert "pragas" in seccions_claves
    seccion = seccions_claves["pragas"]
    assert seccion.etiqueta == "Seguimento de pragas"
    assert seccion.icona == "bug_report"
    assert seccion.no_menu is True

    assert ICONAS["observacion"] == "bug_report"
    assert SECCION_DO_TIPO["observacion"] == "pragas"
    assert _MODELOS["observacion"] is ObservacionPraga
    assert _CONSTRUTORES["observacion"] is dialogo_observacion
