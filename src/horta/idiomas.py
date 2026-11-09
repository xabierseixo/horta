"""Xestión de idiomas e traducións mediante gettext e Babel."""

from __future__ import annotations

import gettext
import re
from contextlib import contextmanager
from contextvars import ContextVar
from io import BytesIO
from pathlib import Path
from typing import Iterator

import babel.messages.mofile
import babel.messages.pofile
from nicegui import app

IDIOMA_BASE = "gl"
DIR_LOCALES = Path(__file__).parent / "locales"

_idioma_forzado: ContextVar[str | None] = ContextVar("_idioma_forzado", default=None)
_TRADUCIONS: dict[str, gettext.NullTranslations] = {}
_NOMES_IDIOMAS: dict[str, str] = {}


def cargar_traducions(
    directorio: Path = DIR_LOCALES,
) -> dict[str, gettext.NullTranslations]:
    """Carga os catálogos .po atopados no directorio indicado.

    Para cada directorio/<código>/horta.po, lese con Babel, compílase a .mo
    en memoria e almacénase un GNUTranslations na caché de módulo.
    """
    directorio = Path(directorio)
    if not directorio.exists() or not directorio.is_dir():
        return dict(_TRADUCIONS)

    for sub in sorted(directorio.iterdir()):
        if sub.is_dir():
            po_file = sub / "horta.po"
            if po_file.is_file():
                codigo = sub.name
                with open(po_file, "r", encoding="utf-8") as f:
                    catalog = babel.messages.pofile.read_po(f)
                buf = BytesIO()
                babel.messages.mofile.write_mo(buf, catalog)
                buf.seek(0)
                trans = gettext.GNUTranslations(buf)

                # Babel descarta as cabeceiras que non coñece: lese do texto do .po
                atopado = re.search(r'"Language-Name:\s*([^"\\]+)', po_file.read_text("utf-8"))
                nome = atopado.group(1).strip() if atopado else codigo

                _NOMES_IDIOMAS[codigo] = nome
                _TRADUCIONS[codigo] = trans

    return dict(_TRADUCIONS)


def recargar_traducions(
    directorio: Path = DIR_LOCALES,
) -> dict[str, gettext.NullTranslations]:
    """Baleira a caché e volve cargar as traducións dende o directorio."""
    _TRADUCIONS.clear()
    _NOMES_IDIOMAS.clear()
    return cargar_traducions(Path(directorio))


def idiomas_disponibles() -> dict[str, str]:
    """Lista de idiomas dispoñibles na aplicación (código -> nome).

    Sempre inclúe 'gl' (Galego) como idioma base na primeira posición.
    """
    resultado: dict[str, str] = {IDIOMA_BASE: "Galego"}
    for codigo in sorted(_TRADUCIONS.keys()):
        if codigo == IDIOMA_BASE:
            continue
        nome = _NOMES_IDIOMAS.get(codigo)
        if not nome:
            trans = _TRADUCIONS[codigo]
            info = trans.info() if hasattr(trans, "info") else {}
            nome = info.get("language-name") or info.get("Language-Name") or codigo
        resultado[codigo] = nome
    return resultado


def idioma_actual() -> str:
    """Devolve o código do idioma activo para a petición ou contexto actual.

    Prioridade:
    1. Idioma forzado mediante con_idioma (_idioma_forzado).
    2. Idioma preferido na sesión de usuario (app.storage.user).
    3. Idioma base (gl) se non hai sesión ou o código non está dispoñible.
    """
    codigo = _idioma_forzado.get()
    if codigo is None:
        try:
            codigo = app.storage.user.get("idioma")
        except Exception:
            codigo = None

    if not codigo or codigo not in _TRADUCIONS:
        return IDIOMA_BASE
    return codigo


def _(texto: str) -> str:
    """Traduce a cadea de texto ao idioma activo."""
    if not texto:
        return texto
    idioma = idioma_actual()
    if idioma == IDIOMA_BASE:
        return texto
    trans = _TRADUCIONS.get(idioma)
    if trans is None:
        return texto
    return trans.gettext(texto)


def ngettext(singular: str, plural: str, n: int) -> str:
    """Traduce unha cadea con forma singular e plural segundo a cantidade n."""
    if not singular:
        return singular if n == 1 else plural
    idioma = idioma_actual()
    if idioma == IDIOMA_BASE:
        return singular if n == 1 else plural
    trans = _TRADUCIONS.get(idioma)
    if trans is None:
        return singular if n == 1 else plural
    return trans.ngettext(singular, plural, n)


def N_(texto: str) -> str:
    """Marca unha cadea para extracción sen traducila de inmediato.

    Útil para constantes ou dicionarios definidos ao cargar módulos que se
    traducirán despois con _() no momento de mostralos na interface.
    """
    return texto


@contextmanager
def con_idioma(codigo: str) -> Iterator[None]:
    """Forza temporalmente un idioma dentro do bloque de contexto."""
    token = _idioma_forzado.set(codigo)
    try:
        yield
    finally:
        _idioma_forzado.reset(token)


# Carga inicial das traducións dispoñibles
cargar_traducions()
