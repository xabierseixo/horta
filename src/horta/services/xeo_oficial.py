"""Consultas á cartografía oficial ao premer no mapa: recinto SIGPAC (FEGA) e parcela do
Catastro. As imaxes do mapa van por services.teselas (con caché)."""

from __future__ import annotations

import gzip
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.parcelas import actualizar_parcela, crear_parcela, xeometria_debuxada

_SIGPAC_PUNTO = ("https://sigpac-hubcloud.es/servicioconsultassigpac/query/recinfobypoint/4326/"
                 "{lon}/{lat}.json")
_CATASTRO_PUNTO = ("https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/"
                   "Consulta_RCCOOR?SRS=EPSG:4326&Coordenada_X={lon}&Coordenada_Y={lat}")
_ESPERA_S = 15


class SenConexion(Exception):
    """O servizo oficial non respondeu."""


def _descargar(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=_ESPERA_S) as resposta:
            datos: bytes = resposta.read()
    except OSError as erro:
        raise SenConexion(str(erro)) from erro
    # O SIGPAC responde comprimido
    return gzip.decompress(datos) if datos[:2] == b"\x1f\x8b" else datos


@dataclass(frozen=True)
class Recinto:
    provincia: str
    municipio: str
    agregado: str
    zona: str
    poligono: str
    parcela: str
    recinto: str
    uso: str | None
    puntos: list[tuple[float, float]]  # (lat, lon) do contorno

    @property
    def referencia(self) -> str:
        return (f"{self.provincia}:{self.municipio}:{self.agregado}:{self.zona}:"
                f"{self.poligono}:{self.parcela}:{self.recinto}")


def puntos_wkt(wkt: str) -> list[tuple[float, float]]:
    """(lat, lon) do primeiro anel dun POLYGON ou MULTIPOLYGON WKT en lonxitude latitude."""
    anel = re.search(r"\(\(+([^()]+)\)", wkt or "")
    if anel is None:
        return []
    puntos = []
    for par in anel.group(1).split(","):
        lon, lat = (float(v) for v in par.split()[:2])
        puntos.append((lat, lon))
    return puntos[:-1] if len(puntos) > 1 and puntos[0] == puntos[-1] else puntos


def _campo(fila: dict[str, Any], *nomes: str) -> str:
    minusculas = {k.lower(): v for k, v in fila.items()}
    return next((str(minusculas[n]) for n in nomes if minusculas.get(n) is not None), "")


def ler_recintos(datos: Any) -> list[Recinto]:
    """A resposta de recinfobypoint (lista de recintos co WKT)."""
    filas = datos if isinstance(datos, list) else [datos] if isinstance(datos, dict) else []
    recintos = []
    for fila in filas:
        wkt = _campo(fila, "wkt", "geometria", "geometry")
        recintos.append(Recinto(
            _campo(fila, "provincia"), _campo(fila, "municipio"), _campo(fila, "agregado"),
            _campo(fila, "zona"), _campo(fila, "poligono"), _campo(fila, "parcela"),
            _campo(fila, "recinto"), _campo(fila, "uso_sigpac", "uso") or None,
            puntos_wkt(wkt)))
    return recintos


def recinto_no_punto(lat: float, lon: float) -> Recinto | None:
    recintos = ler_recintos(json.loads(_descargar(_SIGPAC_PUNTO.format(lat=lat, lon=lon))))
    return recintos[0] if recintos else None


def ler_referencia_catastral(xml: bytes) -> str | None:
    """A referencia catastral (pc1 + pc2) da resposta de Consulta_RCCOOR."""
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return None
    partes = {el.tag.rsplit("}", 1)[-1]: (el.text or "") for el in raiz.iter()}
    referencia = partes.get("pc1", "") + partes.get("pc2", "")
    return referencia or None


def referencia_catastral_no_punto(lat: float, lon: float) -> str | None:
    return ler_referencia_catastral(_descargar(_CATASTRO_PUNTO.format(lat=lat, lon=lon)))


def _campos_do_recinto(recinto: Recinto) -> dict[str, Any]:
    if len(recinto.puntos) < 3:
        raise OperacionNonPermitidaError("O SIGPAC non devolveu o contorno do recinto")
    geojson, hectareas, centro = xeometria_debuxada(recinto.puntos)
    return {"sigpac_provincia": recinto.provincia, "sigpac_concello": recinto.municipio,
            "sigpac_agregado": recinto.agregado, "sigpac_zona": recinto.zona,
            "sigpac_poligono": recinto.poligono, "sigpac_parcela": recinto.parcela,
            "sigpac_subparcela": recinto.recinto, "uso_aproveitamento": recinto.uso,
            "geometria": geojson, "superficie": hectareas, "lat": centro[0], "lon": centro[1]}


def crear_parcela_do_recinto(session: Session, actor: Usuario, horta_id: int, nome: str,
                             recinto: Recinto) -> Parcela:
    campos = _campos_do_recinto(recinto)
    parcela = crear_parcela(session, actor, horta_id, nome.strip() or
                            f"Recinto {recinto.poligono}-{recinto.parcela}-{recinto.recinto}")
    return actualizar_parcela(session, actor, parcela, **campos)


def completar_parcela_co_recinto(session: Session, actor: Usuario, parcela: Parcela,
                                 recinto: Recinto) -> Parcela:
    return actualizar_parcela(session, actor, parcela, **_campos_do_recinto(recinto))


# --- Catastro: datos non protexidos e contorno dunha referencia

_CATASTRO_DNPRC = ("https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/"
                   "Consulta_DNPRC?Provincia=&Municipio=&RC={rc}")
_CATASTRO_WFS = ("https://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx?service=wfs&version=2.0.0&"
                 "request=GetFeature&STOREDQUERIE_ID=GetParcel&refcat={rc}&srsname=EPSG:4326")
_CLASES = {"RU": "Rústico", "UR": "Urbano"}


@dataclass(frozen=True)
class ParcelaCatastral:
    referencia: str
    localizacion: str | None = None
    clase: str | None = None
    uso: str | None = None
    superficie_m2: float | None = None
    # (cultivo, intensidade, m²) de cada subparcela
    cultivos: tuple[tuple[str, str, float | None], ...] = ()
    puntos: tuple[tuple[float, float], ...] = ()


def _texto(raiz: ET.Element, etiqueta: str) -> str | None:
    for el in raiz.iter():
        if el.tag.rsplit("}", 1)[-1] == etiqueta and (el.text or "").strip():
            return (el.text or "").strip()
    return None


def _numero(texto: str | None) -> float | None:
    try:
        return float(texto) if texto else None
    except ValueError:
        return None


def ler_dnprc(xml: bytes, referencia: str) -> ParcelaCatastral:
    """Datos non protexidos dun inmoble (Consulta_DNPRC). Se falla, só a referencia."""
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return ParcelaCatastral(referencia)
    cultivos = []
    for el in raiz.iter():
        if el.tag.rsplit("}", 1)[-1] == "spr":
            cultivos.append((_texto(el, "dcc") or _texto(el, "ccc") or "?",
                             _texto(el, "ip") or "", _numero(_texto(el, "ssp"))))
    clase = _texto(raiz, "cn")
    return ParcelaCatastral(
        referencia, _texto(raiz, "ldt"), _CLASES.get(clase or "", clase), _texto(raiz, "luso"),
        _numero(_texto(raiz, "ssf") or _texto(raiz, "sfc")), tuple(cultivos))


def ler_gml_parcela(xml: bytes) -> tuple[list[tuple[float, float]], float | None]:
    """Contorno (lat, lon) e superficie (m²) da parcela no GML do WFS INSPIRE (EPSG:4326:
    latitude primeiro)."""
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError:
        return [], None
    lista = _texto(raiz, "posList")
    puntos: list[tuple[float, float]] = []
    if lista:
        valores = [float(v) for v in lista.split()]
        puntos = [(valores[i], valores[i + 1]) for i in range(0, len(valores) - 1, 2)]
        if len(puntos) > 1 and puntos[0] == puntos[-1]:
            puntos = puntos[:-1]
    return puntos, _numero(_texto(raiz, "areaValue"))


def parcela_catastral_no_punto(lat: float, lon: float) -> ParcelaCatastral | None:
    referencia = referencia_catastral_no_punto(lat, lon)
    if referencia is None:
        return None
    datos = ler_dnprc(_descargar(_CATASTRO_DNPRC.format(rc=referencia)), referencia)
    try:
        puntos, area = ler_gml_parcela(_descargar(_CATASTRO_WFS.format(rc=referencia)))
    except SenConexion:
        puntos, area = [], None
    return ParcelaCatastral(datos.referencia, datos.localizacion, datos.clase, datos.uso,
                            datos.superficie_m2 or area, datos.cultivos, tuple(puntos))


def _campos_da_catastral(parcela: ParcelaCatastral) -> dict[str, Any]:
    campos: dict[str, Any] = {"referencia_catastral": parcela.referencia}
    if len(parcela.puntos) >= 3:
        geojson, hectareas, centro = xeometria_debuxada(list(parcela.puntos))
        campos |= {"geometria": geojson, "superficie": hectareas, "lat": centro[0],
                   "lon": centro[1]}
    elif parcela.superficie_m2:
        campos["superficie"] = round(parcela.superficie_m2 / 10000, 4)
    return campos


def crear_parcela_do_catastro(session: Session, actor: Usuario, horta_id: int, nome: str,
                              parcela: ParcelaCatastral) -> Parcela:
    nova = crear_parcela(session, actor, horta_id, nome.strip() or parcela.localizacion
                         or f"Parcela {parcela.referencia}")
    return actualizar_parcela(session, actor, nova, **_campos_da_catastral(parcela))


def completar_parcela_co_catastro(session: Session, actor: Usuario, parcela: Parcela,
                                  datos: ParcelaCatastral) -> Parcela:
    return actualizar_parcela(session, actor, parcela, **_campos_da_catastral(datos))
