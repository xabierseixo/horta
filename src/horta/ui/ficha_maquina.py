"""Ficha da máquina: datos, historial e fotos."""

from __future__ import annotations

from collections.abc import Callable

from horta.db import get_session
from horta.models.maquina import Maquina
from horta.services.catalogos import describir
from horta.services.fotos import MODELOS
from horta.services.historial import historial_maquina
from horta.services.maquinaria import listar_maquinas
from horta.ui.ficha import abrir_ficha
from horta.ui.fotos import abrir_fotos
from horta.ui.numeros import formatar_decimal, texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual


def datos_maquina(
    maquina: Maquina,
    describir_codigo: Callable[[str, str], str],
) -> list[tuple[str, str]]:
    """Devolve as parellas etiqueta/valor que teñan valor para a ficha da máquina."""
    resultado: list[tuple[str, str]] = []

    if getattr(maquina, "alias", None) is not None and str(maquina.alias).strip():
        resultado.append(("Nome", str(maquina.alias).strip()))

    if getattr(maquina, "tipo_une", None) is not None and str(maquina.tipo_une).strip():
        tipo_txt = describir_codigo("tipo_maquinaria_une", str(maquina.tipo_une).strip())
        if tipo_txt and tipo_txt.strip():
            resultado.append(("Tipo de máquina", tipo_txt.strip()))

    if getattr(maquina, "marca_modelo", None) is not None and str(maquina.marca_modelo).strip():
        resultado.append(("Marca e modelo", str(maquina.marca_modelo).strip()))

    if getattr(maquina, "num_roma", None) is not None and str(maquina.num_roma).strip():
        resultado.append(("Nº ROMA", str(maquina.num_roma).strip()))

    if getattr(maquina, "num_reganip", None) is not None and str(maquina.num_reganip).strip():
        resultado.append(("Nº REGANIP", str(maquina.num_reganip).strip()))

    if (
        getattr(maquina, "id_equipo_non_inscribible", None) is not None
        and str(maquina.id_equipo_non_inscribible).strip()
    ):
        resultado.append(
            ("Equipo non inscribible", str(maquina.id_equipo_non_inscribible).strip())
        )

    if getattr(maquina, "potencia", None) is not None:
        pot_txt = formatar_decimal(maquina.potencia)
        if (
            getattr(maquina, "unidade_potencia", None) is not None
            and str(maquina.unidade_potencia).strip()
        ):
            uni = describir_codigo("unidade_medida", str(maquina.unidade_potencia).strip())
            if uni and uni.strip():
                pot_txt = f"{pot_txt} {uni.strip()}".strip()
        if pot_txt:
            resultado.append(("Potencia", pot_txt))

    if getattr(maquina, "tipo_enerxia", None) is not None and str(maquina.tipo_enerxia).strip():
        enerxia_txt = describir_codigo("tipo_enerxia", str(maquina.tipo_enerxia).strip())
        if enerxia_txt and enerxia_txt.strip():
            resultado.append(("Tipo de enerxía", enerxia_txt.strip()))

    if getattr(maquina, "data_adquisicion", None) is not None:
        data_adq_txt = texto_data(maquina.data_adquisicion)
        if data_adq_txt:
            resultado.append(("Data de adquisición", data_adq_txt))

    if getattr(maquina, "data_ultima_inspeccion", None) is not None:
        data_insp_txt = texto_data(maquina.data_ultima_inspeccion)
        if data_insp_txt:
            resultado.append(("Última inspección", data_insp_txt))

    if (
        getattr(maquina, "propia", None) is not None
        or getattr(maquina, "alugada", None) is not None
    ):
        e_propia = bool(getattr(maquina, "propia", False)) and not bool(
            getattr(maquina, "alugada", False)
        )
        resultado.append(("Propia ou alugada", "Propia" if e_propia else "Alugada"))

    if getattr(maquina, "activa", None) is not None:
        resultado.append(("Activa", "Si" if maquina.activa else "Non"))

    return resultado


def abrir_ficha_maquina(
    horta_id: int,
    maquina_id: int,
    pode_editar: bool,
    ao_editar: Callable[[], None] | None = None,
) -> None:
    """Abre o diálogo coa ficha da máquina: datos, historial e fotos."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        maquinas = listar_maquinas(session, actor, horta_id, so_activas=False)
        maquina = next((m for m in maquinas if m.id == maquina_id), None)
        if maquina is None:
            return

        titulo = maquina.alias
        datos = datos_maquina(maquina, lambda cat, cod: describir(session, cat, cod))
        feitos = historial_maquina(session, actor, maquina)
        linas_historial = [
            f"{texto_data(f.data)} · {f.que}" if f.data else f.que
            for f in feitos
        ]

    accion_fotos = (
        (lambda: abrir_fotos(horta_id, "maquina", maquina_id, titulo, pode_editar))
        if "maquina" in MODELOS
        else None
    )
    accions = [("Editar", "edit", ao_editar)] if ao_editar is not None else None
    abrir_ficha(titulo, datos, linas_historial, fotos=accion_fotos, accions=accions)
