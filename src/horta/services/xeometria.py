"""Operacións cos lindes debuxados no mapa: dividir cunha liña, xuntar dous anacos e deixar
un cultivo dentro do seu recinto (a DGC vai sempre dentro dun recinto SIGPAC, RD 1054/2022
art. 2.1.d). Os puntos van en (lat, lon), coma no resto da app."""

from __future__ import annotations

from shapely.geometry import LineString, Polygon
from shapely.geometry.base import BaseGeometry
from shapely.ops import split, unary_union

from horta.services.errors import OperacionNonPermitidaError

Punto = tuple[float, float]
# Marxe para que dous anacos que comparten linde se xunten aínda que os puntos non
# coincidan ao milímetro (en graos: uns 10 cm)
_MARXE = 1e-6


def _poligono(puntos: list[Punto]) -> Polygon:
    if len(puntos) < 3:
        raise OperacionNonPermitidaError("Un polígono precisa polo menos tres puntos")
    p = Polygon([(lon, lat) for lat, lon in puntos])
    return p if p.is_valid else p.buffer(0)


def _puntos(xeometria: BaseGeometry) -> list[Punto]:
    """O polígono máis grande da xeometría, en (lat, lon)."""
    poligonos = [g for g in getattr(xeometria, "geoms", [xeometria])
                 if isinstance(g, Polygon) and not g.is_empty]
    if not poligonos:
        return []
    maior = max(poligonos, key=lambda g: g.area)
    return [(round(lat, 7), round(lon, 7)) for lon, lat in list(maior.exterior.coords)[:-1]]


def dividir(puntos: list[Punto], linea: list[Punto]) -> list[list[Punto]]:
    if len(linea) < 2:
        raise OperacionNonPermitidaError("A liña precisa polo menos dous puntos")
    partes = split(_poligono(puntos), LineString([(lon, lat) for lat, lon in linea]))
    anacos = [_puntos(g) for g in partes.geoms if g.area > 0]
    if len(anacos) < 2:
        raise OperacionNonPermitidaError("A liña ten que cruzar o anaco de lado a lado")
    return anacos


def xuntar(a: list[Punto], b: list[Punto]) -> list[Punto]:
    unido = unary_union([_poligono(a).buffer(_MARXE), _poligono(b).buffer(_MARXE)]
                        ).buffer(-_MARXE)
    if not isinstance(unido, Polygon):
        raise OperacionNonPermitidaError("Só se poden xuntar dous anacos que se toquen")
    return _puntos(unido.simplify(_MARXE / 10))


def recortar(puntos: list[Punto], limite: list[Punto]) -> list[Punto]:
    """O debuxo, recortado polo linde (o cultivo non pode saír do recinto)."""
    dentro = _puntos(_poligono(puntos).intersection(_poligono(limite)))
    if len(dentro) < 3:
        raise OperacionNonPermitidaError("O debuxo ten que quedar dentro do recinto")
    return dentro
