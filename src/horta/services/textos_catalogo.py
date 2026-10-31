from __future__ import annotations

import csv
from functools import cache
from pathlib import Path

RUTA_CATALOGOS_GL = Path(__file__).resolve().parents[1] / "data" / "catalogos_gl.csv"


@cache
def _textos_galegos() -> dict[tuple[str, str], str]:
    with RUTA_CATALOGOS_GL.open(encoding="utf-8") as f:
        return {
            (fila["catalogo"], fila["codigo"]): texto
            for fila in csv.DictReader(f, delimiter=";")
            if (texto := (fila.get("texto_gl") or "").strip())
        }


def texto_catalogo(catalogo: str, codigo: str, descricion: str) -> str:
    return _textos_galegos().get((catalogo, codigo), descricion)
