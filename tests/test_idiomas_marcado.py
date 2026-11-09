"""Probas do marcado de textos da interface para internacionalización (paso 187b)."""

from __future__ import annotations

from pathlib import Path

import pytest

from horta.idiomas import _, con_idioma, recargar_traducions
from horta.ui.boton_confirmar import boton_para
from horta.ui.layout import SECCIONS
from horta.ui.taboas import TEXTOS_TABOA

_PO_PROBA_MARCADO = """msgid ""
msgstr ""
"Language-Name: Proba Marcado\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "Inicio"
msgstr "Home-xx"

msgid "Pechar sesión"
msgstr "Log out-xx"

msgid "Produción"
msgstr "Production-xx"

msgid "Filas por páxina"
msgstr "Rows per page-xx"

msgid "Dar de baixa"
msgstr "Deactivate-xx"

msgid "Eliminar"
msgstr "Delete-xx"
"""


@pytest.fixture(autouse=True)
def _restablecer_traducions():
    """Restaura as traducións reais ao rematar cada proba."""
    yield
    recargar_traducions()


def test_seccions_layout_marcado(tmp_path: Path) -> None:
    """Os títulos e grupos de SECCIONS pasados por _() tradúcense con con_idioma
    e fóra quedan na base."""
    xx_dir = tmp_path / "xx"
    xx_dir.mkdir(parents=True, exist_ok=True)
    (xx_dir / "horta.po").write_text(_PO_PROBA_MARCADO, encoding="utf-8")
    recargar_traducions(tmp_path)

    seccion_inicio = next(s for s in SECCIONS if s.clave == "resumo")
    seccion_parcelas = next(s for s in SECCIONS if s.clave == "parcelas")

    # Constantes en memoria sen traducir
    assert seccion_inicio.etiqueta == "Inicio"
    assert seccion_parcelas.grupo == "Produción"

    # Fóra de con_idioma saen en galego
    assert _(seccion_inicio.etiqueta) == "Inicio"
    assert _(seccion_parcelas.grupo or "") == "Produción"
    assert _("Pechar sesión") == "Pechar sesión"

    # Dentro de con_idioma saen traducidos
    with con_idioma("xx"):
        assert _(seccion_inicio.etiqueta) == "Home-xx"
        assert _(seccion_parcelas.grupo or "") == "Production-xx"
        assert _("Pechar sesión") == "Log out-xx"

    # Fóra volven a saír en galego
    assert _(seccion_inicio.etiqueta) == "Inicio"
    assert _(seccion_parcelas.grupo or "") == "Produción"
    assert _("Pechar sesión") == "Pechar sesión"


def test_taboas_e_botons_marcado(tmp_path: Path) -> None:
    """TEXTOS_TABOA e boton_para tradúcense dentro de con_idioma."""
    xx_dir = tmp_path / "xx"
    xx_dir.mkdir(parents=True, exist_ok=True)
    (xx_dir / "horta.po").write_text(_PO_PROBA_MARCADO, encoding="utf-8")
    recargar_traducions(tmp_path)

    assert "Filas por páxina" in str(TEXTOS_TABOA)
    assert boton_para("Dar de baixa este elemento")[0] == "Dar de baixa"
    assert boton_para("Eliminar este elemento")[0] == "Eliminar"

    with con_idioma("xx"):
        assert "Rows per page-xx" in str(TEXTOS_TABOA)
        assert boton_para("Dar de baixa este elemento")[0] == "Deactivate-xx"
        assert boton_para("Eliminar este elemento")[0] == "Delete-xx"

    assert "Filas por páxina" in str(TEXTOS_TABOA)
    assert boton_para("Dar de baixa este elemento")[0] == "Dar de baixa"
