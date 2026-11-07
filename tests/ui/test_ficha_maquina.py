"""Probas para a ficha da máquina (datos_maquina)."""

from __future__ import annotations

from datetime import date

from horta.models.maquina import Maquina
from horta.ui.ficha_maquina import datos_maquina


def _describir_proba(catalogo: str, codigo: str) -> str:
    taboa = {
        ("tipo_maquinaria_une", "01"): "Tractor de rodas",
        ("unidade_medida", "40"): "CV",
        ("tipo_enerxia", "D"): "Gasóleo",
    }
    return taboa.get((catalogo, codigo), codigo)


def test_datos_maquina_completa() -> None:
    """Unha máquina con todos os datos mostra as súas etiquetas e valores formatados."""
    maquina = Maquina(
        alias="Tractor Ebro",
        tipo_une="01",
        marca_modelo="Ebro 160D",
        num_roma="12345",
        num_reganip="67890",
        potencia=60.0,
        unidade_potencia="40",
        tipo_enerxia="D",
        data_adquisicion=date(2020, 5, 15),
        data_ultima_inspeccion=date(2025, 4, 10),
        propia=True,
        alugada=False,
        activa=True,
    )
    datos = datos_maquina(maquina, _describir_proba)

    esperados = [
        ("Nome", "Tractor Ebro"),
        ("Tipo de máquina", "Tractor de rodas"),
        ("Marca e modelo", "Ebro 160D"),
        ("Nº ROMA", "12345"),
        ("Nº REGANIP", "67890"),
        ("Potencia", "60 CV"),
        ("Tipo de enerxía", "Gasóleo"),
        ("Data de adquisición", "15/05/2020"),
        ("Última inspección", "10/04/2025"),
        ("Propia ou alugada", "Propia"),
        ("Activa", "Si"),
    ]
    assert datos == esperados


def test_datos_maquina_minima() -> None:
    """Unha máquina só co alias devolve unicamente a parella de Nome."""
    maquina = Maquina(alias="Mochila pulverizadora")
    datos = datos_maquina(maquina, _describir_proba)

    assert datos == [("Nome", "Mochila pulverizadora")]


def test_datos_maquina_alugada_non_activa() -> None:
    """Unha máquina alugada e inactiva mostra Alugada e Non."""
    maquina = Maquina(
        alias="Colleitadora",
        propia=False,
        alugada=True,
        activa=False,
    )
    datos = datos_maquina(maquina, _describir_proba)

    assert ("Nome", "Colleitadora") in datos
    assert ("Propia ou alugada", "Alugada") in datos
    assert ("Activa", "Non") in datos


def test_datos_maquina_equipo_non_inscribible() -> None:
    """Un equipo non inscribible mostra a etiqueta correspondente."""
    maquina = Maquina(
        alias="Motoserra",
        id_equipo_non_inscribible="MS-200",
    )
    datos = datos_maquina(maquina, _describir_proba)

    assert ("Nome", "Motoserra") in datos
    assert ("Equipo non inscribible", "MS-200") in datos
