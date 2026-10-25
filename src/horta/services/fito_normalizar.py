"""Limpa os textos do JSON do MAPA (prazos, aplicacións, intervalos e unidades).

Trasladado de fitosanitarios/normalizar.py, só cos campos que usa horta.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import Any


def texto(v: Any) -> str | None:
    if v is None:
        return None
    s = re.sub(r"[ \t]+", " ", str(v).replace("\r\n", "\n").replace("\r", "\n")).strip()
    return s or None


def clave(v: Any) -> str:
    """Forma de comparación: maiúsculas, sen acentos nin espazos repetidos."""
    s = "".join(c for c in unicodedata.normalize("NFD", str(v or ""))
                if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.upper()).strip()


def data(v: Any) -> date | None:
    """'1974-12-13T00:00:00', '2027/07/31', '31/07/2027' -> date."""
    s = (v or "").strip()
    if m := re.match(r"(\d{4})[-/](\d{2})[-/](\d{2})", s):
        return date(int(m[1]), int(m[2]), int(m[3]))
    if m := re.match(r"(\d{2})[-/](\d{2})[-/](\d{4})", s):
        return date(int(m[3]), int(m[2]), int(m[1]))
    return None


def numero(v: Any) -> float | None:
    """0 no MAPA significa «non indicado»."""
    return float(v) if v not in (None, "", 0, 0.0) else None


_BALEIRO = {"", "-", "--", "*", "."}
_NON_PROCEDE = re.compile(
    r"(NO ?PROCEDE|N0 ?PROCEDE|N\.? ?P\.?|N\.? ?A\.?|N/A|NO APLICA|NO RELEVANTE)\.?")


def prazo_seguridade(v: Any) -> tuple[str, int | None]:
    """(tipo, días). tipo: dias | non_procede | condicional | ver_condicionamento | sen_dato.

    Nos condicionais os días son o prazo máis longo do texto («10 aire libre, 3 invernadoiro»
    → 10), para avisar sen risco.
    """
    t = clave(v)
    if t in _BALEIRO:
        return "sen_dato", None
    if _NON_PROCEDE.fullmatch(t):
        return "non_procede", 0
    if m := re.fullmatch(r"(\d+) ?(DIAS?|D)?\.?", t):
        return "dias", int(m[1])
    # Os números despois de BBCH son estados fenolóxicos; as horas arredóndanse a 1 día
    sen_bbch = re.sub(r"BBCH ?\d+", "", t)
    dias = [int(n) for n in re.findall(r"(\d+) ?(?!\d| ?HORA)", sen_bbch)]
    dias += [1 for _ in re.findall(r"\d+ ?HORA", sen_bbch)]
    if not dias and re.search(r"\bNP\b|NO ?PROCEDE", t):
        dias = [0]
    if not dias:
        return ("ver_condicionamento" if "VER" in t else "condicional"), None
    return "condicional", max(dias)


def aplicacions_max(v: Any) -> int | None:
    """'Máx. 3' / '3' / '1-3' / '1 o 2' -> o máximo."""
    t = clave(v).replace("(*)", "").replace("*", "").strip()
    if t in _BALEIRO:
        return None
    if m := re.fullmatch(r"(?:MAX(?:IMO)?\.? ?)?(\d+)\.?", t):
        return int(m[1])
    if m := re.search(r"(\d+) ?(?:-|O) ?\(?(\d+)\)?", t):
        return int(m[2])
    if m := re.match(r"(?:MAX(?:IMO)?\.? ?)?(\d+)\b(?! ?(?:H|/|CADA))", t):
        return int(m[1])
    return None


_UNIDADES_TEMPO = {"": 1, "D": 1, "DIA": 1, "DIAS": 1, "SEMANA": 7, "SEMANAS": 7,
                   "MES": 30, "MESES": 30, "ANO": 365, "ANOS": 365}


def intervalo_min_dias(v: Any) -> int | None:
    """'7 días' -> 7; '7-14 d' -> 7; 'Mín. 10' -> 10; '3-4 semanas' -> 21."""
    t = clave(v).replace("(*)", "").replace("*", "").strip(" .()")
    if t in _BALEIRO or _NON_PROCEDE.fullmatch(t):
        return None
    unidade = r" ?(D|DIAS?|SEMANAS?|MES(?:ES)?|ANOS?)?\.?"
    if m := re.fullmatch(r"(\d+)" + unidade, t):
        return int(m[1]) * _UNIDADES_TEMPO[m[2] or ""]
    if m := re.fullmatch(r"(\d+) ?(?:-|A) ?(\d+)" + unidade, t):
        return int(m[1]) * _UNIDADES_TEMPO[m[3] or ""]
    if m := re.fullmatch(
        r"(?:MIN(?:IMO)?\.? ?(\d+)|(\d+) ?(?:DIAS? )?\(?MINIMO\)?)" + unidade, t
    ):
        return int(m[1] or m[2]) * _UNIDADES_TEMPO[m[3] or ""]
    return None


def unidade_dose(v: Any) -> str | None:
    """Unidade canónica: Kg/ha → kg/ha, cc → ml, /Hl → /hl; sen o «(ver nota)»."""
    s = texto(v)
    if not s or s.lower() == "sin asignar":
        return None
    s = re.sub(r"\s*\(ver [^)]*\)\s*", "", s, flags=re.I).strip()
    if not s:
        return None
    s = re.sub(r"\bKg\b", "kg", s)
    s = re.sub(r"\bcc\b", "ml", s)
    s = re.sub(r"/Hl\b", "/hl", s)
    s = re.sub(r"/Tm\b", "/t", s)
    s = re.sub(r"/Qm\b", "/q", s)
    return re.sub(r"/Ha\.?$", "/ha", s)


def nome_cientifico(agente: str) -> str:
    """'Mildiu de la patata y el tomate, Phytophthora infestans' -> 'PHYTOPHTHORA INFESTANS'."""
    return clave(agente.rsplit(",", 1)[-1])
