"""Probas da sección de conectar o móbil á app do campo en «A miña conta»."""

from __future__ import annotations

from datetime import datetime

from horta.ui.pages.conta import formato_data_alta, formato_ultimo_uso, url_conexion_campo


def test_url_conexion_campo_orixe_sen_barra_final() -> None:
    url = url_conexion_campo("http://localhost:8081", "clave-secreta-123")
    assert url == "http://localhost:8081/campo/#clave=clave-secreta-123"


def test_url_conexion_campo_orixe_con_barra_final() -> None:
    url = url_conexion_campo("http://localhost:8081/", "clave-secreta-123")
    assert url == "http://localhost:8081/campo/#clave=clave-secreta-123"


def test_url_conexion_campo_orixe_https_con_subruta() -> None:
    url = url_conexion_campo("https://horta.gal/app/", "token-456")
    assert url == "https://horta.gal/app/campo/#clave=token-456"


def test_url_conexion_campo_orixe_baleira() -> None:
    url = url_conexion_campo("", "clave-xyz")
    assert url == "/campo/#clave=clave-xyz"


def test_formato_data_alta() -> None:
    dt = datetime(2026, 11, 8, 15, 30)
    assert formato_data_alta(dt) == "08/11/2026"
    assert formato_data_alta(None) == ""


def test_formato_ultimo_uso() -> None:
    assert formato_ultimo_uso(None) == "Nunca"
    dt = datetime(2026, 11, 8, 22, 10)
    assert formato_ultimo_uso(dt) == "08/11/2026"
