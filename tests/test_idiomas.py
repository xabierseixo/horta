"""Probas da base do sistema multilingüe (gettext e Babel)."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from horta.idiomas import (
    N_,
    _,
    con_idioma,
    idioma_actual,
    idiomas_disponibles,
    ngettext,
    recargar_traducions,
)
from horta.models.usuario import RolGlobal, Usuario
from horta.services.auth import hash_password
from horta.services.errors import OperacionNonPermitidaError
from horta.services.usuarios import cambiar_idioma

_PO_PROBA = """msgid ""
msgstr ""
"Language-Name: Proba\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

msgid "Gardar"
msgstr "Save-xx"

msgid "{n} leira"
msgid_plural "{n} leiras"
msgstr[0] "{n} plot-xx"
msgstr[1] "{n} plots-xx"
"""

_PO_SEN_NOME = """msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Gardar"
msgstr "Save-yy"
"""


@pytest.fixture(autouse=True)
def _restablecer_traducions():
    """Restaura as traducións reais ao rematar cada proba."""
    yield
    recargar_traducions()


def test_sen_po_so_base(tmp_path: Path) -> None:
    """Sen ningún .po, só está dispoñible o galego e os textos saen en galego."""
    recargar_traducions(tmp_path)

    assert idiomas_disponibles() == {"gl": "Galego"}
    assert _("Gardar") == "Gardar"
    assert idioma_actual() == "gl"
    assert N_("Texto sen traducir") == "Texto sen traducir"
    assert ngettext("{n} leira", "{n} leiras", 1) == "{n} leira"
    assert ngettext("{n} leira", "{n} leiras", 2) == "{n} leiras"


def test_cun_po_de_proba(tmp_path: Path) -> None:
    """Cun .po cargado, con_idioma traduce, respecta plurais e fóra volve á base."""
    xx_dir = tmp_path / "xx"
    xx_dir.mkdir(parents=True, exist_ok=True)
    (xx_dir / "horta.po").write_text(_PO_PROBA, encoding="utf-8")

    recargar_traducions(tmp_path)
    disponibles = idiomas_disponibles()

    assert disponibles["gl"] == "Galego"
    assert disponibles["xx"] == "Proba"

    with con_idioma("xx"):
        assert idioma_actual() == "xx"
        assert _("Gardar") == "Save-xx"
        assert _("Texto sen tradución") == "Texto sen tradución"
        assert ngettext("{n} leira", "{n} leiras", 1) == "{n} plot-xx"
        assert ngettext("{n} leira", "{n} leiras", 2) == "{n} plots-xx"
        assert ngettext("{n} leira", "{n} leiras", 0) == "{n} plots-xx"

    assert idioma_actual() == "gl"
    assert _("Gardar") == "Gardar"
    assert ngettext("{n} leira", "{n} leiras", 1) == "{n} leira"
    assert ngettext("{n} leira", "{n} leiras", 2) == "{n} leiras"


def test_con_idioma_codigo_non_existe(tmp_path: Path) -> None:
    """Forzar un idioma inexistente devolve o idioma base."""
    recargar_traducions(tmp_path)

    with con_idioma("codigo_inexistente"):
        assert idioma_actual() == "gl"
        assert _("Gardar") == "Gardar"


def test_po_sen_language_name(tmp_path: Path) -> None:
    """Se o .po non ten cabeceira Language-Name, úsase o código como nome."""
    yy_dir = tmp_path / "yy"
    yy_dir.mkdir(parents=True, exist_ok=True)
    (yy_dir / "horta.po").write_text(_PO_SEN_NOME, encoding="utf-8")

    recargar_traducions(tmp_path)
    disponibles = idiomas_disponibles()

    assert disponibles["yy"] == "yy"
    with con_idioma("yy"):
        assert _("Gardar") == "Save-yy"


def test_cambiar_idioma_usuario(session: Session, tmp_path: Path) -> None:
    """cambiar_idioma garda un código válido e rexeita códigos non dispoñibles."""
    usuario = Usuario(
        nome="Xan",
        email="xan@example.com",
        password_hash=hash_password("segredo"),
        rol=RolGlobal.USUARIO,
        activo=True,
    )
    session.add(usuario)
    session.commit()
    assert usuario.idioma == "gl"

    xx_dir = tmp_path / "xx"
    xx_dir.mkdir(parents=True, exist_ok=True)
    (xx_dir / "horta.po").write_text(_PO_PROBA, encoding="utf-8")
    recargar_traducions(tmp_path)

    cambiar_idioma(session, usuario, "xx")
    assert usuario.idioma == "xx"

    with pytest.raises(OperacionNonPermitidaError):
        cambiar_idioma(session, usuario, "desconecido")

    cambiar_idioma(session, usuario, "gl")
    assert usuario.idioma == "gl"
