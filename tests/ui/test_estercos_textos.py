"""Probas das funcións puras e configuración da pantalla de estercos."""

from __future__ import annotations

from horta.models.esterco import MovementoEsterco
from horta.ui.layout import SECCIONS
from horta.ui.pages.diario import _CONSTRUTORES, _MODELOS, ICONAS, SECCION_DO_TIPO
from horta.ui.pages.estercos import (
    COLUMNAS_TABOA,
    dialogo_esterco,
    texto_faltas_documento,
    texto_resumo_material,
    texto_resumo_n,
    texto_tipo_movemento,
)


def test_texto_tipo_movemento():
    assert texto_tipo_movemento("cesion") == "Cesión"
    assert texto_tipo_movemento("recepcion") == "Recepción"


def test_texto_faltas_documento():
    assert texto_faltas_documento([]) == ""
    assert (
        texto_faltas_documento(["Nitróxeno total (N)", "Orixe da composición"])
        == "Nitróxeno total (N), Orixe da composición"
    )


def test_texto_resumo_material():
    assert (
        texto_resumo_material("Purín de porco", 10.5, "t")
        == "Purín de porco: 10.5 t"
    )
    assert (
        texto_resumo_material("Esterco de bovino", 5.0, "m3")
        == "Esterco de bovino: 5 m3"
    )


def test_texto_resumo_n():
    assert texto_resumo_n(25.0) == "25 kg de N"
    assert texto_resumo_n(12.34) == "12.34 kg de N"


def test_columnas_taboa():
    campos = [c["field"] for c in COLUMNAS_TABOA]
    assert campos == [
        "data",
        "tipo",
        "outra_parte",
        "material",
        "cantidade",
        "n_total",
        "orixe_composicion",
        "faltas",
    ]
    col_faltas = next(c for c in COLUMNAS_TABOA if c["field"] == "faltas")
    assert col_faltas["label"] == "Faltan datos"
    assert col_faltas.get("classes") == "text-warning"


def test_seccion_estercos_en_layout():
    seccion = next((s for s in SECCIONS if s.clave == "estercos"), None)
    assert seccion is not None
    assert seccion.etiqueta == "Estercos e purín"
    assert seccion.icona == "compost"
    assert seccion.no_menu is True


def test_rexistro_movemento_esterco_en_diario():
    assert ICONAS["movemento_esterco"] == "compost"
    assert SECCION_DO_TIPO["movemento_esterco"] == "estercos"
    assert _MODELOS["movemento_esterco"] is MovementoEsterco
    assert _CONSTRUTORES["movemento_esterco"] is dialogo_esterco
