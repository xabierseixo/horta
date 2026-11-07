"""Probas para a ficha do cultivo (datos_cultivo)."""

from __future__ import annotations

from datetime import date

from horta.models.cultivo import Cultivo
from horta.ui.ficha_cultivo import datos_cultivo


def _describir_proba(catalogo: str, codigo: str) -> str:
    taboa = {
        ("sistema_cultivo", "1"): "Aire libre",
        ("sistema_explotacion", "S"): "Secano",
        ("destino_cultivo", "1"): "Consumo humano en fresco",
        ("certificacion_ecoloxica", "2"): "Certificado",
    }
    return taboa.get((catalogo, codigo), codigo)


def test_datos_cultivo_completo_plantacion() -> None:
    """Un cultivo con todos os datos mostra as súas etiquetas, datas e Plantación."""
    cultivo = Cultivo(
        especie="Maceira",
        variedade="Fuji",
        superficie_ha=1.5,
        tipo_inicio="plantacion",
        data_inicio=date(2026, 3, 15),
        data_fin=date(2026, 11, 30),
        sistema_cultivo="1",
        sistema_explotacion="S",
        destino="1",
        certificacion_ecoloxica="2",
        num_arbores=120,
        marco_plantacion="4x4",
    )
    datos = datos_cultivo(cultivo, _describir_proba)

    esperados = [
        ("Cultivo", "Maceira Fuji"),
        ("Variedade", "Fuji"),
        ("Superficie cultivada", "1,50 ha"),
        ("Plantación", "15/03/2026"),
        ("Remate", "30/11/2026"),
        ("Sistema de cultivo", "Aire libre"),
        ("Secano ou regadío", "Secano"),
        ("Destino", "Consumo humano en fresco"),
        ("Ecolóxico", "Certificado"),
        ("Árbores", "120"),
        ("Marco de plantación", "4x4"),
    ]
    assert datos == esperados


def test_datos_cultivo_so_especie() -> None:
    """Un cultivo só coa especie devolve unicamente a parella de Cultivo."""
    cultivo = Cultivo(especie="Tomate")
    datos = datos_cultivo(cultivo, _describir_proba)

    assert datos == [("Cultivo", "Tomate")]


def test_datos_cultivo_sementeira_e_superficie_m2() -> None:
    """Tipo sementeira pon a etiqueta Sementeira e superficies menores de 1 ha van en m²."""
    cultivo = Cultivo(
        especie="Cenoria",
        superficie_ha=0.035,
        tipo_inicio="sementeira",
        data_inicio=date(2026, 5, 10),
    )
    datos = datos_cultivo(cultivo, _describir_proba)

    assert ("Cultivo", "Cenoria") in datos
    assert ("Superficie cultivada", "350 m²") in datos
    assert ("Sementeira", "10/05/2026") in datos
    assert len(datos) == 3


def test_datos_cultivo_sen_datas() -> None:
    """Se non hai data_inicio nin data_fin non saen nin inicio nin remate."""
    cultivo = Cultivo(
        especie="Pemento",
        tipo_inicio="plantacion",
        data_inicio=None,
        data_fin=None,
    )
    datos = datos_cultivo(cultivo, _describir_proba)
    etiquetas = [e for e, _ in datos]

    assert "Plantación" not in etiquetas
    assert "Sementeira" not in etiquetas
    assert "Remate" not in etiquetas
