"""Ficha da persoa: datos e historial."""

from __future__ import annotations

from collections.abc import Callable

from horta.db import get_session
from horta.models.persoa import Persoa
from horta.services.catalogos import describir
from horta.services.equipo import historial
from horta.services.persoas import listar_persoas
from horta.ui.etiquetas import TIPOS_CARNE
from horta.ui.ficha import abrir_ficha
from horta.ui.numeros import texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual

_REXISTROS = (
    ("rega", "REGA (ES + 12 díxitos)"),
    ("reaga", "REAGA"),
    ("nima", "NIMA"),
    ("ropveg", "Nº ROPVEG"),
    ("rexistro_dixital", "Nº de rexistro dixital de alimentos"),
    ("num_asesoramento", "Nº de identificación da entidade de asesoramento"),
)

_CONTACTO = (
    ("enderezo", "Enderezo"),
    ("localidade", "Localidade"),
    ("codigo_postal", "Código postal"),
    ("provincia", "Provincia"),
    ("pais", "País, se non é España"),
)


def datos_persoa(
    persoa: Persoa,
    describir_codigo: Callable[[str, str], str],
) -> list[tuple[str, str]]:
    """Devolve as parellas etiqueta/valor que teñan valor para a ficha da persoa."""
    resultado: list[tuple[str, str]] = []

    if getattr(persoa, "nome", None) is not None and str(persoa.nome).strip():
        resultado.append(("Nome ou razón social", str(persoa.nome).strip()))

    if getattr(persoa, "apelidos", None) is not None and str(persoa.apelidos).strip():
        resultado.append(("Apelidos", str(persoa.apelidos).strip()))

    if getattr(persoa, "nif", None) is not None and str(persoa.nif).strip():
        resultado.append(("NIF", str(persoa.nif).strip()))

    if getattr(persoa, "ropo_numero", None) is not None and str(persoa.ropo_numero).strip():
        resultado.append(("Nº ROPO", str(persoa.ropo_numero).strip()))

    if persoa.ropo_tipo_carne is not None:
        codigo = persoa.ropo_tipo_carne.value
        resultado.append(("Tipo de carné", TIPOS_CARNE.get(codigo, codigo)))

    if getattr(persoa, "ropo_caducidade", None) is not None:
        data_cad_txt = texto_data(persoa.ropo_caducidade)
        if data_cad_txt:
            resultado.append(("Caducidade do carné", data_cad_txt))

    if getattr(persoa, "regfer_numero", None) is not None and str(persoa.regfer_numero).strip():
        resultado.append(("Nº REGFER", str(persoa.regfer_numero).strip()))

    for campo, etiqueta in _REXISTROS:
        valor = getattr(persoa, campo, None)
        if valor is not None and str(valor).strip():
            resultado.append((etiqueta, str(valor).strip()))

    for campo, etiqueta in _CONTACTO:
        valor = getattr(persoa, campo, None)
        if valor is not None and str(valor).strip():
            resultado.append((etiqueta, str(valor).strip()))

    return resultado


def abrir_ficha_persoa(
    horta_id: int,
    persoa_id: int,
    accions: list[tuple[str, str, Callable[[], None]]] | None = None,
) -> None:
    """Abre o diálogo coa ficha da persoa: datos e historial."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        persoas = listar_persoas(session, actor, horta_id, so_activas=False)
        persoa = next((p for p in persoas if p.id == persoa_id), None)
        if persoa is None or persoa.horta_id != horta_id:
            return

        titulo = f"{persoa.nome} {persoa.apelidos or ''}".strip()
        datos = datos_persoa(persoa, lambda cat, cod: describir(session, cat, cod))
        feitos = historial(session, actor, persoa)
        linas_historial: list[str] = []
        for f in feitos:
            data = f"{texto_data(f.data)} · " if f.data else ""
            importe = f" · {f.importe:.2f} €" if f.importe is not None else ""
            pendente = " · pendente" if f.pendente else ""
            linas_historial.append(f"{data}{f.que}{importe}{pendente}")

    abrir_ficha(titulo, datos, linas_historial, accions=accions)
