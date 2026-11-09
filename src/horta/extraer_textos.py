"""Extractor de textos para traducir (úsao `pybabel extract` vía `babel.cfg`).

O extractor de Python de Babel le o código por tokens e, ata Python 3.12, non ve as
chamadas a `_()` que van dentro dunha f-string (`f'label="{_("Data")}"'`). Este lé o
código coa árbore de `ast`, que si as ve.
"""

from __future__ import annotations

import ast
from collections.abc import Collection, Iterator, Mapping
from typing import IO, Any


def extraer(
    fileobj: IO[bytes],
    keywords: Mapping[str, Any] | Collection[str],
    comment_tags: Collection[str],
    options: Mapping[str, Any],
) -> Iterator[tuple[int, str, str | tuple[str, ...], list[str]]]:
    """Devolve (liña, función, texto ou textos, comentarios) de cada texto marcado."""
    arbore = ast.parse(fileobj.read().decode(options.get("encoding", "utf-8")))
    for nodo in ast.walk(arbore):
        if not (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Name)
            and nodo.func.id in keywords
        ):
            continue
        textos = [
            arg.value
            for arg in nodo.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        ]
        if nodo.func.id == "ngettext":
            if len(textos) >= 2:
                yield nodo.lineno, nodo.func.id, (textos[0], textos[1]), []
        elif textos and nodo.args and isinstance(nodo.args[0], ast.Constant):
            yield nodo.lineno, nodo.func.id, textos[0], []
