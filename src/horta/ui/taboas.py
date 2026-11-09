"""Textos comúns das táboas en galego (Quasar non trae galego e mostra inglés)."""

from __future__ import annotations

from horta.idiomas import N_, _


def textos_taboa() -> str:
    """Devolve as propiedades Quasar das táboas no idioma actual."""
    filas_por_paxina = _("Filas por páxina")
    non_hai_resultados = _("Non hai resultados")
    de = _("de")
    fila_unha = _("1 fila escollida")
    filas_varias = _("{n} filas escollidas").replace("{n}", "${n}")
    return (
        f'rows-per-page-label="{filas_por_paxina}" '
        f'no-results-label="{non_hai_resultados}" '
        ':pagination-label="(primeira, ultima, total) => '
        f'`${{primeira}}-${{ultima}} {de} ${{total}}`" '
        f":selected-rows-label=\"(n) => n === 1 ? '{fila_unha}' : `{filas_varias}`\""
    )


class _TextosTaboa(str):
    def __str__(self) -> str:
        return textos_taboa()

    def __contains__(self, item: object) -> bool:
        return str(item) in textos_taboa()

    def __eq__(self, other: object) -> bool:
        return textos_taboa() == other

    def __format__(self, especificacion: str) -> str:
        # As f-strings chaman a __format__, non a __str__
        return format(textos_taboa(), especificacion)

    def __repr__(self) -> str:
        return repr(textos_taboa())


_CADEAS_TABOA = (
    N_("Filas por páxina"),
    N_("Non hai resultados"),
    N_("de"),
    N_("1 fila escollida"),
    N_("{n} filas escollidas"),
)

TEXTOS_TABOA = _TextosTaboa(
    'rows-per-page-label="Filas por páxina" no-results-label="Non hai resultados" '
    ':pagination-label="(primeira, ultima, total) => `${primeira}-${ultima} de ${total}`" '
    ":selected-rows-label=\"(n) => n === 1 ? '1 fila escollida' : `${n} filas escollidas`\""
)
