"""Probas do servizo conversor de formatos de exportación."""

from __future__ import annotations

from datetime import date
from io import BytesIO
import xml.etree.ElementTree as ET
import zipfile

from openpyxl import Workbook
import pytest

from horta.services.formatos import (
    FORMATOS,
    a_csv,
    a_ods,
    a_pdf,
    a_xml,
    converter,
    follas,
)


def _crear_libro_proba() -> bytes:
    """Crea un libro Excel pequeno con dúas follas e varios tipos de datos."""
    wb = Workbook()

    # Folla 1: "Resumo"
    ws1 = wb.active
    assert ws1 is not None
    ws1.title = "Resumo"

    # Cela combinada en A1:B1
    ws1.merge_cells("A1:B1")
    ws1["A1"] = "Título combinado"

    # Fila 2: data, número con decimais, cela baleira no medio (C2), enteiro
    ws1["A2"] = date(2026, 11, 8)
    ws1["B2"] = 1234.5
    # C2 queda baleira
    ws1["D2"] = 42

    # Fila 3: número con decimais fixos (number_format)
    ws1["A3"] = 12.5
    ws1["A3"].number_format = "0.00"

    # Filas e columnas finais baleiras que deben recortarse
    ws1["E3"] = None
    ws1["A5"] = None

    # Folla 2: "Detalle"
    ws2 = wb.create_sheet(title="Detalle")
    ws2["A1"] = "Texto segunda folla"
    ws2["B1"] = 100

    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def _crear_libro_unha_folla() -> bytes:
    """Crea un libro Excel cunha soa folla para probar a exportación a CSV."""
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.title = "Unica"
    ws["A1"] = "Dato 1"
    ws["B1"] = 250
    bio = BytesIO()
    wb.save(bio)
    return bio.getvalue()


def test_formatos_disponibles():
    assert "xlsx" in FORMATOS
    assert "pdf" in FORMATOS
    assert "ods" in FORMATOS
    assert "csv" in FORMATOS
    assert "xml" in FORMATOS


def test_follas_textos_datas_decimais_recorte():
    xlsx = _crear_libro_proba()
    resultado = follas(xlsx)

    assert len(resultado) == 2
    nome1, filas1 = resultado[0]
    assert nome1 == "Resumo"

    # Cela combinada: valor na primeira cela, segunda baleira
    assert filas1[0][0] == "Título combinado"
    assert filas1[0][1] == ""

    # Data en DD/MM/AAAA, coma decimal galega, cela baleira no medio, enteiro sen decimais
    assert filas1[1][0] == "08/11/2026"
    assert filas1[1][1] == "1234,5"
    assert filas1[1][2] == ""
    assert filas1[1][3] == "42"

    # Number_format con decimais fixos respectado: 12.5 con 0.00 -> 12,50
    assert filas1[2][0] == "12,50"

    # Recorte de filas finais baleiras (a fila 5 desaparece, quedan só 3 filas)
    assert len(filas1) == 3

    # Recorte de columnas finais baleiras (a columna E desaparece, quedan 4 columnas: A, B, C, D)
    assert len(filas1[1]) == 4

    # Segunda folla
    nome2, filas2 = resultado[1]
    assert nome2 == "Detalle"
    assert filas2[0] == ["Texto segunda folla", "100"]


def test_a_csv_unha_folla():
    xlsx = _crear_libro_unha_folla()
    contido, ext = a_csv(xlsx)

    assert ext == "csv"
    assert contido.startswith(b"\xef\xbb\xbf")  # UTF-8 con BOM
    texto = contido.decode("utf-8-sig")
    assert ";" in texto
    assert "Dato 1;250" in texto


def test_a_csv_varias_follas():
    xlsx = _crear_libro_proba()
    contido, ext = a_csv(xlsx)

    assert ext == "zip"
    with zipfile.ZipFile(BytesIO(contido)) as zf:
        nomes = zf.namelist()
        assert len(nomes) == 2
        assert "01-Resumo.csv" in nomes
        assert "02-Detalle.csv" in nomes

        for nome in nomes:
            ficheiro_bytes = zf.read(nome)
            assert ficheiro_bytes.startswith(b"\xef\xbb\xbf")
            assert b";" in ficheiro_bytes


def test_a_xml():
    xlsx = _crear_libro_proba()
    contido = a_xml(xlsx, raiz="caderno")

    assert contido.startswith(b"<?xml")
    root = ET.fromstring(contido)
    assert root.tag == "caderno"

    follas_elem = root.findall("folla")
    assert len(follas_elem) == 2
    assert follas_elem[0].get("nome") == "Resumo"
    assert follas_elem[1].get("nome") == "Detalle"

    # Comprobar unha cela concreta
    cela = root.find(".//folla[@nome='Resumo']/fila[@n='1']/cela[@col='A']")
    assert cela is not None
    assert cela.text == "Título combinado"

    # As celas baleiras non deben aparecer no XML
    celas_fila1 = root.findall(".//folla[@nome='Resumo']/fila[@n='1']/cela")
    assert len(celas_fila1) == 1
    assert celas_fila1[0].get("col") == "A"


def test_a_ods():
    xlsx = _crear_libro_proba()
    contido = a_ods(xlsx)

    with zipfile.ZipFile(BytesIO(contido)) as zf:
        assert "content.xml" in zf.namelist()
        xml_texto = zf.read("content.xml").decode("utf-8")
        assert "Resumo" in xml_texto
        assert "Detalle" in xml_texto


def test_a_pdf():
    xlsx = _crear_libro_proba()
    contido = a_pdf(xlsx, titulo="Caderno de explotación")

    assert contido.startswith(b"%PDF")


def test_converter():
    xlsx = _crear_libro_proba()

    # Formato xlsx devolve os mesmos bytes
    contido_xlsx, ext_xlsx = converter(xlsx, "xlsx", "Caderno", "caderno")
    assert ext_xlsx == "xlsx"
    assert contido_xlsx == xlsx

    # Formato pdf
    contido_pdf, ext_pdf = converter(xlsx, "pdf", "Caderno", "caderno")
    assert ext_pdf == "pdf"
    assert contido_pdf.startswith(b"%PDF")

    # Formato ods
    contido_ods, ext_ods = converter(xlsx, "ods", "Caderno", "caderno")
    assert ext_ods == "ods"
    assert zipfile.is_zipfile(BytesIO(contido_ods))

    # Formato xml
    contido_xml, ext_xml = converter(xlsx, "xml", "Caderno", "caderno")
    assert ext_xml == "xml"
    assert contido_xml.startswith(b"<?xml")

    # Formato csv con varias follas devolve zip
    contido_csv, ext_csv = converter(xlsx, "csv", "Caderno", "caderno")
    assert ext_csv == "zip"
    assert zipfile.is_zipfile(BytesIO(contido_csv))

    # Formato descoñecido levanta ValueError
    with pytest.raises(ValueError):
        converter(xlsx, "formato_inventado", "Caderno", "caderno")
