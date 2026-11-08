"""Probas das funcións de texto para documentos e avisos (tarefa 167)."""

from __future__ import annotations

from datetime import date, timedelta
from types import SimpleNamespace

from horta.ui.pages.documentos import texto_aviso_documento, texto_estado_documento


def test_texto_estado_sen_caducidade_esta_vixente() -> None:
    doc = SimpleNamespace(nome="Estatutos", data_caducidade=None)
    hoxe = date(2026, 11, 8)
    assert texto_estado_documento(doc, hoxe) == "Vixente"


def test_texto_estado_caducidade_distante_esta_vixente() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Seguro", data_caducidade=hoxe + timedelta(days=60))
    assert texto_estado_documento(doc, hoxe) == "Vixente"


def test_texto_estado_limite_aviso_30_dias() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Inspección", data_caducidade=hoxe + timedelta(days=30))
    assert texto_estado_documento(doc, hoxe) == "Caduca en 30 días"


def test_texto_estado_varios_dias() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Carné", data_caducidade=hoxe + timedelta(days=7))
    assert texto_estado_documento(doc, hoxe) == "Caduca en 7 días"


def test_texto_estado_un_dia() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Certificado", data_caducidade=hoxe + timedelta(days=1))
    assert texto_estado_documento(doc, hoxe) == "Caduca en 1 día"


def test_texto_estado_caduca_hoxe() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Autorización", data_caducidade=hoxe)
    assert texto_estado_documento(doc, hoxe) == "Caduca hoxe"


def test_texto_estado_caducado() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Seguro vello", data_caducidade=hoxe - timedelta(days=1))
    assert texto_estado_documento(doc, hoxe) == "Caducado"


def test_texto_aviso_caducado() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="CRAEGA 2025", data_caducidade=date(2026, 10, 15))
    assert texto_aviso_documento(doc, hoxe) == "O documento «CRAEGA 2025» caducou o 15/10/2026"


def test_texto_aviso_caduca_hoxe() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Seguro", data_caducidade=hoxe)
    assert texto_aviso_documento(doc, hoxe) == "O documento «Seguro» caduca hoxe"


def test_texto_aviso_caduca_en_un_dia() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="ITV", data_caducidade=hoxe + timedelta(days=1))
    assert texto_aviso_documento(doc, hoxe) == "O documento «ITV» caduca en 1 día"


def test_texto_aviso_caduca_en_varios_dias() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Carné ROPO", data_caducidade=hoxe + timedelta(days=15))
    assert texto_aviso_documento(doc, hoxe) == "O documento «Carné ROPO» caduca en 15 días"


def test_texto_aviso_sen_caducidade() -> None:
    hoxe = date(2026, 11, 8)
    doc = SimpleNamespace(nome="Estatutos", data_caducidade=None)
    assert texto_aviso_documento(doc, hoxe) == "O documento «Estatutos»"
