"""Ficha da parcela en Terras: datos do caderno, zonas, historial e fotos."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela, SecanoRegadio
from horta.services.catalogos import valores_vixentes
from horta.services.cultivos import listar_cultivos, nome_cultivo
from horta.services.diario import TIPOS
from horta.services.historial import historial_parcela
from horta.services.textos_catalogo import texto_catalogo
from horta.services.zonas import listar_zonas
from horta.ui.fotos import abrir_fotos
from horta.ui.numeros import texto_data
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.superficie import formatar_superficie

_CAMPOS_SIGPAC = (
    ("sigpac_provincia", "Provincia"),
    ("sigpac_concello", "Concello"),
    ("sigpac_agregado", "Agregado"),
    ("sigpac_zona", "Zona"),
    ("sigpac_poligono", "Polígono"),
    ("sigpac_parcela", "Parcela"),
    ("sigpac_subparcela", "Recinto"),
)


def datos_caderno(
    parcela: Parcela,
    nomes_tenencia: dict[str, str],
    nomes_causa: dict[str, str],
) -> list[tuple[str, str]]:
    """Devolve as parellas etiqueta/valor dos datos do caderno da parcela con valor."""
    resultado: list[tuple[str, str]] = []

    for campo, etiqueta in _CAMPOS_SIGPAC:
        valor = getattr(parcela, campo, None)
        if valor is not None and str(valor).strip():
            resultado.append((etiqueta, str(valor).strip()))

    if parcela.uso_aproveitamento:
        resultado.append(("Uso SIXPAC", str(parcela.uso_aproveitamento).strip()))

    if parcela.superficie is not None:
        sup_txt = formatar_superficie(parcela.superficie)
        if sup_txt:
            resultado.append(("Superficie SIXPAC", sup_txt))

    if parcela.secano_regadio is not None:
        rega = {
            SecanoRegadio.SECANO: "Secano",
            SecanoRegadio.REGADIO: "Regadío",
            "secano": "Secano",
            "regadio": "Regadío",
        }.get(parcela.secano_regadio)
        if rega:
            resultado.append(("Secano/Regadío", rega))

    if parcela.rexime_tenencia:
        codigo_tenencia = str(parcela.rexime_tenencia).strip()
        nome_tenencia = nomes_tenencia.get(codigo_tenencia, codigo_tenencia)
        if nome_tenencia:
            resultado.append(("Réxime de tenencia", str(nome_tenencia)))

    if parcela.data_alta:
        data_alta_txt = texto_data(parcela.data_alta)
        if data_alta_txt:
            resultado.append(("Data de alta", data_alta_txt))

    e_baixa = (
        getattr(parcela, "estado", None) == "baixa"
        or bool(getattr(parcela, "data_baixa", None))
        or bool(getattr(parcela, "causa_baixa", None))
    )
    if e_baixa:
        if getattr(parcela, "data_baixa", None):
            data_baixa_txt = texto_data(parcela.data_baixa)
            if data_baixa_txt:
                resultado.append(("Data de baixa", data_baixa_txt))
        if getattr(parcela, "causa_baixa", None):
            codigo_causa = str(parcela.causa_baixa).strip()
            nome_causa = nomes_causa.get(codigo_causa, codigo_causa)
            if nome_causa:
                resultado.append(("Causa da baixa", str(nome_causa)))

    return resultado


def _texto_cultivo(c: Cultivo) -> str:
    nome = nome_cultivo(c)
    if c.data_inicio:
        return f"{nome}, desde {texto_data(c.data_inicio)}"
    return nome


def seccions_ficha_parcela(horta_id: int, parcela_id: int, pode_editar: bool) -> None:
    """Debuxa na ficha da parcela os bloques de caderno, zonas, historial e fotos."""
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        parcela = session.get(Parcela, parcela_id)
        if parcela is None or parcela.horta_id != horta_id:
            return

        nomes_tenencia = {
            v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
            for v in valores_vixentes(session, "rexime_tenencia")
        }
        nomes_causa = {
            v.codigo: texto_catalogo(v.catalogo, v.codigo, v.descricion)
            for v in valores_vixentes(session, "causa_baixa")
        }
        datos = datos_caderno(parcela, nomes_tenencia, nomes_causa)
        zonas = listar_zonas(session, actor, parcela)
        cultivos_abertos = [c for c in listar_cultivos(session, actor, horta_id)
                            if c.parcela_id == parcela.id and c.data_fin is None]
        ano_actual = date.today().year
        traballos = [
            t for t in historial_parcela(session, actor, parcela)
            if t.data and t.data.year == ano_actual
        ]
        traballos.sort(key=lambda t: t.data or date.min, reverse=True)
        ultimos_traballos = traballos[:10]
        p_id = parcela.id
        p_nome = parcela.nome

    # 1. Datos do caderno
    if datos:
        ui.label("Datos do caderno").classes("text-weight-medium q-mt-sm")
        for etiqueta, valor in datos:
            ui.label(f"{etiqueta}: {valor}").classes("texto-suave")

    # 2. Zonas e o que hai en cada unha
    ui.label("Zonas e cultivos").classes("text-weight-medium q-mt-sm")
    por_zona: dict[int | None, list[str]] = defaultdict(list)
    for c in cultivos_abertos:
        por_zona[c.zona_id].append(_texto_cultivo(c))

    if not zonas and not cultivos_abertos:
        ui.label("Sen cultivos agora").classes("texto-suave")
    else:
        for z in zonas:
            cs = por_zona.get(z.id, [])
            if cs:
                ui.label(f"{z.nome}: {', '.join(cs)}").classes("texto-suave")
            else:
                ui.label(z.nome).classes("texto-suave")
        if por_zona.get(None):
            ui.label(f"Sen zona: {', '.join(por_zona[None])}").classes("texto-suave")
        if not cultivos_abertos:
            ui.label("Sen cultivos agora").classes("texto-suave")

    # 3. Historial deste ano
    ui.label("Historial deste ano").classes("text-weight-medium q-mt-sm")
    if ultimos_traballos:
        for t in ultimos_traballos:
            data_str = f"{t.data:%d/%m}" if t.data else ""
            tipo_str = TIPOS.get(t.tipo, t.tipo)
            ui.label(f"{data_str} · {tipo_str} · {t.que}").classes("texto-suave")
    else:
        ui.label("Aínda non hai traballos este ano").classes("texto-suave")

    # 4. Fotos
    ui.button(
        "Fotos",
        icon="photo_camera",
        on_click=lambda i=p_id, n=p_nome: abrir_fotos(horta_id, "parcela", i, n, pode_editar),
    ).props("outline").classes("w-full q-mt-sm")
