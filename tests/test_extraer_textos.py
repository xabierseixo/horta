"""Probas do extractor de textos para traducir."""

from __future__ import annotations

import io

from horta.extraer_textos import extraer

_CODIGO = '''
from horta.idiomas import N_, _, ngettext

TITULO = N_("Inicio")
ui.label(_("Gardar"))
ui.table().props(f'no-data-label="{_("Non hai datos")}" flat')
texto = f'{n} · {ngettext("{n} lectura", "{n} lecturas", n).format(n=n)}'
ui.label(_(variable))
'''


def _mensaxes(codigo: str) -> list[tuple[int, str, str | tuple[str, str]]]:
    return [
        (linea, funcion, mensaxe)
        for linea, funcion, mensaxe, _comentarios in extraer(
            io.BytesIO(codigo.encode("utf-8")), ["_", "N_", "ngettext"], [], {}
        )
    ]


def test_extrae_textos_normais_e_constantes() -> None:
    mensaxes = _mensaxes(_CODIGO)
    assert (4, "N_", "Inicio") in mensaxes
    assert (5, "_", "Gardar") in mensaxes


def test_extrae_textos_dentro_de_f_strings() -> None:
    mensaxes = _mensaxes(_CODIGO)
    assert (6, "_", "Non hai datos") in mensaxes
    assert (7, "ngettext", ("{n} lectura", "{n} lecturas")) in mensaxes


def test_ignora_chamadas_sen_texto_literal() -> None:
    assert len(_mensaxes(_CODIGO)) == 4
