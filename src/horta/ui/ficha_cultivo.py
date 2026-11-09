"""Ficha do cultivo: datos do caderno, historial e fotos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from horta.db import get_session
from horta.idiomas import _
from horta.models.cultivo import Cultivo
from horta.services.catalogos import describir
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.diario import TIPOS
from horta.services.fotos import MODELOS
from horta.services.historial import historial_cultivo
from horta.services.necesidades_rega import necesidade_rega
from horta.ui.ficha import abrir_ficha
from horta.ui.fotos import abrir_fotos
from horta.ui.necesidades_rega import texto_necesidade
from horta.ui.numeros import texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import formatar_superficie


def datos_cultivo(
    cultivo: Cultivo,
    describir_codigo: Callable[[str, str], str],
) -> list[tuple[str, str]]:
    """Devolve as parellas etiqueta/valor que teñan valor para a ficha do cultivo."""
    resultado: list[tuple[str, str]] = []

    nome = nome_cultivo(cultivo)
    if nome and nome.strip():
        resultado.append((_("Cultivo"), nome.strip()))

    if cultivo.variedade is not None and str(cultivo.variedade).strip():
        resultado.append((_("Variedade"), str(cultivo.variedade).strip()))

    if cultivo.superficie_ha is not None:
        sup_txt = formatar_superficie(cultivo.superficie_ha)
        if sup_txt:
            resultado.append((_("Superficie cultivada"), sup_txt))

    if cultivo.data_inicio is not None:
        data_ini_txt = texto_data(cultivo.data_inicio)
        if data_ini_txt:
            etiqueta = _("Plantación") if cultivo.tipo_inicio == "plantacion" else _("Sementeira")
            resultado.append((etiqueta, data_ini_txt))

    if cultivo.data_fin is not None:
        data_fin_txt = texto_data(cultivo.data_fin)
        if data_fin_txt:
            resultado.append((_("Remate"), data_fin_txt))

    if cultivo.sistema_cultivo is not None and str(cultivo.sistema_cultivo).strip():
        sis_cul = describir_codigo("sistema_cultivo", str(cultivo.sistema_cultivo).strip())
        if sis_cul and sis_cul.strip():
            resultado.append((_("Sistema de cultivo"), sis_cul.strip()))

    if cultivo.sistema_explotacion is not None and str(cultivo.sistema_explotacion).strip():
        sis_exp = describir_codigo(
            "sistema_explotacion", str(cultivo.sistema_explotacion).strip()
        )
        if sis_exp and sis_exp.strip():
            resultado.append((_("Secano ou regadío"), sis_exp.strip()))

    if cultivo.destino is not None and str(cultivo.destino).strip():
        dest = describir_codigo("destino_cultivo", str(cultivo.destino).strip())
        if dest and dest.strip():
            resultado.append((_("Destino"), dest.strip()))

    if (
        cultivo.certificacion_ecoloxica is not None
        and str(cultivo.certificacion_ecoloxica).strip()
    ):
        eco = describir_codigo(
            "certificacion_ecoloxica", str(cultivo.certificacion_ecoloxica).strip()
        )
        if eco and eco.strip():
            resultado.append((_("Ecolóxico"), eco.strip()))

    if cultivo.num_arbores is not None:
        resultado.append((_("Árbores"), str(cultivo.num_arbores)))

    if cultivo.marco_plantacion is not None and str(cultivo.marco_plantacion).strip():
        resultado.append((_("Marco de plantación"), str(cultivo.marco_plantacion).strip()))

    return resultado


def abrir_ficha_cultivo(horta_id: int, cultivo_id: int, pode_editar: bool) -> None:
    """Abre o diálogo coa ficha do cultivo: datos, historial completo e fotos."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        cultivos = listar_cultivos(session, actor, horta_id)
        cultivo = next((c for c in cultivos if c.id == cultivo_id), None)
        if cultivo is None:
            return

        nome = nome_cultivo(cultivo)
        datos = datos_cultivo(cultivo, lambda cat, cod: describir(session, cat, cod))
        nec = necesidade_rega(session, actor, cultivo.id)
        if nec.estado != "secano":
            datos.append((_("Rega, últimos 7 días"), texto_necesidade(nec)))
        traballos = sorted(
            historial_cultivo(session, actor, cultivo),
            key=lambda t: t.data or date.min,
            reverse=True,
        )
        linas_historial = [
            f"{texto_data(t.data)} · {_(TIPOS[t.tipo]) if t.tipo in TIPOS else t.tipo} · {t.que}"
            for t in traballos
        ]

    accion_fotos = (
        (lambda: abrir_fotos(horta_id, "cultivo", cultivo_id, nome, pode_editar))
        if "cultivo" in MODELOS
        else None
    )
    abrir_ficha(nome, datos, linas_historial, fotos=accion_fotos)
