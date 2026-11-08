"""Conversor común de formatos de exportación (PDF, ODS, CSV, XML).

Recibe os bytes dun .xlsx xerado con openpyxl e convérteo ao formato pedido.
"""

from __future__ import annotations

import csv
import html
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime
from decimal import Decimal
from io import BytesIO, StringIO
from typing import Any

import weasyprint
from odf.opendocument import OpenDocumentSpreadsheet
from odf.table import Table, TableCell, TableRow
from odf.text import P
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

FORMATOS: dict[str, str] = {
    "xlsx": "Excel",
    "pdf": "PDF",
    "ods": "ODS (LibreOffice)",
    "csv": "CSV",
    "xml": "XML",
}


def _formatar_valor(valor: object, number_format: str | None = None) -> str:
    """Formata o valor dunha cela segundo as regras de exportación."""
    if valor is None:
        return ""
    if isinstance(valor, (datetime, date)):
        return f"{valor:%d/%m/%Y}"
    if isinstance(valor, bool):
        return str(valor)
    if isinstance(valor, (int, float, Decimal)):
        if number_format:
            m = re.search(r"\.(0+)", number_format)
            if m:
                decimais = len(m.group(1))
                return f"{valor:.{decimais}f}".replace(".", ",")
        if isinstance(valor, int):
            return str(valor)
        if isinstance(valor, float) and valor.is_integer():
            return str(int(valor))
        if isinstance(valor, Decimal) and valor == valor.to_integral():
            return str(int(valor))
        return str(valor).replace(".", ",")
    return str(valor)


def _formatar_cela(cela: Any) -> str:
    """Extrae e formata o contido dunha cela de openpyxl."""
    val = getattr(cela, "value", None)
    nf = getattr(cela, "number_format", None)
    return _formatar_valor(val, str(nf) if nf is not None else None)


def follas(xlsx: bytes) -> list[tuple[str, list[list[str]]]]:
    """Abre o libro Excel e devolve o nome e as filas como textos por cada folla."""
    wb = load_workbook(BytesIO(xlsx))
    resultado: list[tuple[str, list[list[str]]]] = []

    for ws in wb.worksheets:
        max_r = ws.max_row or 0
        max_c = ws.max_column or 0
        if max_r == 0 or max_c == 0:
            resultado.append((ws.title, []))
            continue

        filas = [
            [_formatar_cela(ws.cell(row=r, column=c)) for c in range(1, max_c + 1)]
            for r in range(1, max_r + 1)
        ]

        # Quitar filas finais baleiras
        while filas and all(cel == "" for cel in filas[-1]):
            filas.pop()

        # Quitar columnas finais baleiras
        if filas:
            max_col_con_datos = max(
                (c for fila in filas for c, cel in enumerate(fila) if cel != ""),
                default=-1,
            )
            if max_col_con_datos >= 0:
                filas = [fila[: max_col_con_datos + 1] for fila in filas]
            else:
                filas = []

        resultado.append((ws.title, filas))

    return resultado


def _folla_a_csv_bytes(filas: list[list[str]]) -> bytes:
    """Xera os bytes dun CSV con separador ';' e codificación utf-8-sig."""
    sio = StringIO()
    writer = csv.writer(sio, delimiter=";", lineterminator="\r\n")
    for fila in filas:
        writer.writerow(fila)
    return sio.getvalue().encode("utf-8-sig")


def a_csv(xlsx: bytes) -> tuple[bytes, str]:
    """Converte o libro a CSV (unha folla) ou ZIP de CSVs (varias follas)."""
    lista_follas = follas(xlsx)
    if len(lista_follas) <= 1:
        filas = lista_follas[0][1] if lista_follas else []
        return _folla_a_csv_bytes(filas), "csv"

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for idx, (nome, filas) in enumerate(lista_follas, start=1):
            nome_limpo = re.sub(r'[\\/*?:"<>|]', "_", nome).strip() or f"folla_{idx}"
            nome_ficheiro = f"{idx:02d}-{nome_limpo}.csv"
            zf.writestr(nome_ficheiro, _folla_a_csv_bytes(filas))

    return buf.getvalue(), "zip"


def a_xml(xlsx: bytes, raiz: str) -> bytes:
    """Xera un documento XML coas celas con contido das follas do libro."""
    root = ET.Element(raiz)
    for nome_folla, filas in follas(xlsx):
        elem_folla = ET.SubElement(root, "folla", nome=nome_folla)
        for r_idx, fila in enumerate(filas, start=1):
            celas_con_datos = [
                (c_idx, val)
                for c_idx, val in enumerate(fila, start=1)
                if val != ""
            ]
            if not celas_con_datos:
                continue
            elem_fila = ET.SubElement(elem_folla, "fila", n=str(r_idx))
            for c_idx, val in celas_con_datos:
                elem_cela = ET.SubElement(
                    elem_fila, "cela", col=get_column_letter(c_idx)
                )
                elem_cela.text = val

    ET.indent(root)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def a_ods(xlsx: bytes) -> bytes:
    """Xera unha folla de cálculo ODS (OpenDocument) co contido do libro."""
    doc = OpenDocumentSpreadsheet()
    for nome_folla, filas in follas(xlsx):
        tabela = Table(name=nome_folla)
        for fila in filas:
            tr = TableRow()
            for cel in fila:
                if cel != "":
                    tc = TableCell(valuetype="string")
                    tc.addElement(P(text=cel))
                else:
                    tc = TableCell()
                tr.addElement(tc)
            tabela.addElement(tr)
        doc.spreadsheet.addElement(tabela)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def a_pdf(xlsx: bytes, titulo: str) -> bytes:
    """Xera un documento PDF formatado a partir das follas do libro."""
    wb = load_workbook(BytesIO(xlsx))
    follas_datos = follas(xlsx)

    seccions_html: list[str] = []

    for idx, (ws, (_, filas)) in enumerate(zip(wb.worksheets, follas_datos)):
        nome = ws.title
        num_rows = len(filas)
        num_cols = len(filas[0]) if num_rows > 0 else 0

        # Mapear celas combinadas
        merge_origin: dict[tuple[int, int], tuple[int, int]] = {}
        covered_cells: set[tuple[int, int]] = set()

        for rng in ws.merged_cells.ranges:
            min_r, max_r = rng.min_row, rng.max_row
            min_c, max_c = rng.min_col, rng.max_col
            rowspan = max_r - min_r + 1
            colspan = max_c - min_c + 1
            if rowspan > 1 or colspan > 1:
                merge_origin[(min_r, min_c)] = (rowspan, colspan)
                for r in range(min_r, max_r + 1):
                    for c in range(min_c, max_c + 1):
                        if (r, c) != (min_r, min_c):
                            covered_cells.add((r, c))

        filas_html: list[str] = []
        # A cabeceira de columnas é a primeira fila con varios datos despois dun título
        agarda_cabeceira = True
        for r in range(1, num_rows + 1):
            fila = filas[r - 1]
            con_datos = sum(1 for cel in fila if cel != "")
            if con_datos == 0 and (r, 1) not in merge_origin:
                continue
            if num_cols > 1 and con_datos == 1 and fila[0] != "" and (r, 1) not in merge_origin:
                # Título dunha sección: ocupa toda a liña
                filas_html.append(f'<tr><td class="titulo" colspan="{num_cols}">'
                                  f"{html.escape(fila[0])}</td></tr>")
                agarda_cabeceira = True
                continue
            es_cabeceira = agarda_cabeceira and con_datos > 1
            agarda_cabeceira = False
            tag = "th" if es_cabeceira else "td"
            celas_html: list[str] = []

            for c in range(1, num_cols + 1):
                if (r, c) in covered_cells:
                    continue  # Non se debuxan as celas que tapan as combinadas

                attrs = ""
                if (r, c) in merge_origin:
                    r_span, c_span = merge_origin[(r, c)]
                    r_span = min(r_span, num_rows - r + 1)
                    c_span = min(c_span, num_cols - c + 1)
                    if r_span > 1:
                        attrs += f' rowspan="{r_span}"'
                    if c_span > 1:
                        attrs += f' colspan="{c_span}"'

                texto = html.escape(filas[r - 1][c - 1])
                celas_html.append(f"<{tag}{attrs}>{texto}</{tag}>")

            if celas_html:
                filas_html.append(f"<tr>{''.join(celas_html)}</tr>")

        quebra_estilo = "page-break-before: always;" if idx > 0 else ""
        estilo_div = f' style="{quebra_estilo}"' if quebra_estilo else ""

        seccion = (
            f'<div class="folla"{estilo_div}>\n'
            f"  <h2>{html.escape(nome)}</h2>\n"
            f"  <table>\n"
            f"    <tbody>\n"
            f"      {chr(10).join(filas_html)}\n"
            f"    </tbody>\n"
            f"  </table>\n"
            f"</div>"
        )
        seccions_html.append(seccion)

    doc_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{html.escape(titulo)}</title>
  <style>
    @page {{
      size: A4 landscape;
      margin: 12mm;
    }}
    body {{
      font-family: sans-serif;
      font-size: 8pt;
      color: #000;
      margin: 0;
      padding: 0;
    }}
    h1 {{
      font-size: 14pt;
      margin-top: 0;
      margin-bottom: 6mm;
    }}
    h2 {{
      font-size: 11pt;
      margin-top: 0;
      margin-bottom: 3mm;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      table-layout: fixed;
      font-size: 7pt;
    }}
    td.titulo {{
      font-weight: bold;
      font-size: 9pt;
      background: #eee;
    }}
    th, td {{
      border: 0.5pt solid #555;
      padding: 3px 5px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{
      font-weight: bold;
    }}
  </style>
</head>
<body>
  <h1>{html.escape(titulo)}</h1>
  {chr(10).join(seccions_html)}
</body>
</html>"""

    return weasyprint.HTML(string=doc_html).write_pdf()


def converter(
    xlsx: bytes, formato: str, titulo: str, raiz: str
) -> tuple[bytes, str]:
    """Converte un libro Excel ao formato solicitado.

    Devolve unha tupla co contido en bytes e a extensión correspondente.
    """
    fmt = formato.lower().strip()
    if fmt == "xlsx":
        return xlsx, "xlsx"
    if fmt == "pdf":
        return a_pdf(xlsx, titulo), "pdf"
    if fmt == "ods":
        return a_ods(xlsx), "ods"
    if fmt == "xml":
        return a_xml(xlsx, raiz), "xml"
    if fmt == "csv":
        return a_csv(xlsx)

    raise ValueError(f"Formato non soportado: {formato}")
