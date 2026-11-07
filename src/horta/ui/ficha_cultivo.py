"""Ficha do cultivo: datos do caderno, historial e fotos."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.services.catalogos import describir
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.diario import TIPOS
from horta.services.fotos import MODELOS
from horta.services.historial import historial_cultivo
from horta.ui.fotos import abrir_fotos
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
        resultado.append(("Cultivo", nome.strip()))

    if cultivo.variedade is not None and str(cultivo.variedade).strip():
        resultado.append(("Variedade", str(cultivo.variedade).strip()))

    if cultivo.superficie_ha is not None:
        sup_txt = formatar_superficie(cultivo.superficie_ha)
        if sup_txt:
            resultado.append(("Superficie cultivada", sup_txt))

    if cultivo.data_inicio is not None:
        data_ini_txt = texto_data(cultivo.data_inicio)
        if data_ini_txt:
            etiqueta = "Plantación" if cultivo.tipo_inicio == "plantacion" else "Sementeira"
            resultado.append((etiqueta, data_ini_txt))

    if cultivo.data_fin is not None:
        data_fin_txt = texto_data(cultivo.data_fin)
        if data_fin_txt:
            resultado.append(("Remate", data_fin_txt))

    if cultivo.sistema_cultivo is not None and str(cultivo.sistema_cultivo).strip():
        sis_cul = describir_codigo("sistema_cultivo", str(cultivo.sistema_cultivo).strip())
        if sis_cul and sis_cul.strip():
            resultado.append(("Sistema de cultivo", sis_cul.strip()))

    if cultivo.sistema_explotacion is not None and str(cultivo.sistema_explotacion).strip():
        sis_exp = describir_codigo("sistema_explotacion", str(cultivo.sistema_explotacion).strip())
        if sis_exp and sis_exp.strip():
            resultado.append(("Secano ou regadío", sis_exp.strip()))

    if cultivo.destino is not None and str(cultivo.destino).strip():
        dest = describir_codigo("destino_cultivo", str(cultivo.destino).strip())
        if dest and dest.strip():
            resultado.append(("Destino", dest.strip()))

    if cultivo.certificacion_ecoloxica is not None and str(cultivo.certificacion_ecoloxica).strip():
        eco = describir_codigo(
            "certificacion_ecoloxica", str(cultivo.certificacion_ecoloxica).strip()
        )
        if eco and eco.strip():
            resultado.append(("Ecolóxico", eco.strip()))

    if cultivo.num_arbores is not None:
        resultado.append(("Árbores", str(cultivo.num_arbores)))

    if cultivo.marco_plantacion is not None and str(cultivo.marco_plantacion).strip():
        resultado.append(("Marco de plantación", str(cultivo.marco_plantacion).strip()))

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
        traballos = sorted(
            historial_cultivo(session, actor, cultivo),
            key=lambda t: t.data or date.min,
            reverse=True,
        )
        liñas_historial = [
            (texto_data(t.data), TIPOS.get(t.tipo, t.tipo), t.que)
            for t in traballos
        ]

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        ui.label(nome).classes("text-h6")

        if datos:
            with ui.element("div").style(
                "display:grid; grid-template-columns:auto 1fr; gap:2px 12px"
            ):
                for etiqueta, valor in datos:
                    ui.label(etiqueta).classes("texto-suave")
                    ui.label(valor)

        ui.label("Historial").classes("text-weight-medium q-mt-sm")
        with ui.column().classes("gap-0"):
            if liñas_historial:
                for data_str, tipo_str, que_str in liñas_historial:
                    ui.label(f"{data_str} · {tipo_str} · {que_str}").classes("texto-suave")
            else:
                ui.label("Aínda non hai traballos").classes("texto-suave")

        if "cultivo" in MODELOS:
            ui.button(
                "Fotos",
                icon="photo_camera",
                on_click=lambda: abrir_fotos(
                    horta_id, "cultivo", cultivo_id, nome, pode_editar
                ),
            ).props("outline").classes("w-full q-mt-sm")

        ui.button("Pechar", on_click=dialogo.close).props("flat").classes("w-full q-mt-sm")

    dialogo.open()
