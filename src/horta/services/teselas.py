"""Teselas do mapa con caché no ordenador: ortofoto PNOA (WMTS do IGN), recintos SIGPAC e
Catastro (WMS pedidos por tesela). A primeira vez descárganse; despois sérvense desde o disco,
tamén sen conexión. «Gardar a zona» descarga de antemán os arredores das parcelas."""

from __future__ import annotations

import math
import os
import urllib.request
from collections.abc import Callable
from pathlib import Path

_MUNDO = 20037508.342789244  # metade do lado do mundo en EPSG:3857
_ESPERA_S = 20
# capa → (url, extensión). Nas WMS, {bbox} en EPSG:3857
ORIXES: dict[str, tuple[str, str]] = {
    "pnoa": ("https://www.ign.es/wmts/pnoa-ma?service=WMTS&request=GetTile&version=1.0.0"
             "&format=image/jpeg&layer=OI.OrthoimageCoverage&style=default"
             "&tilematrixset=GoogleMapsCompatible&tilematrix={z}&tilerow={y}&tilecol={x}", "jpg"),
    "sigpac": ("https://sigpac-hubcloud.es/wms?service=WMS&request=GetMap&version=1.3.0"
               "&layers=AU.Sigpac:recinto&styles=&crs=EPSG:3857&bbox={bbox}&width=256"
               "&height=256&format=image/png&transparent=true", "png"),
    "catastro": ("https://ovc.catastro.meh.es/cartografia/INSPIRE/spadgcwms.aspx?service=WMS"
                 "&request=GetMap&version=1.3.0&layers=CP.CadastralParcel&styles=&crs=EPSG:3857"
                 "&bbox={bbox}&width=256&height=256&format=image/png&transparent=true", "png"),
}
# Zooms que se gardan para usar sen conexión (parcela enteira ata o detalle)
ZOOMS_ZONA = range(14, 20)
MAXIMO_TESELAS = 6000


def cartafol_teselas() -> Path:
    return Path(os.environ.get("HORTA_TESELAS_DIR")
                or Path.home() / ".local" / "share" / "horta" / "teselas")


def bbox_tesela(z: int, x: int, y: int) -> tuple[float, float, float, float]:
    """Límites dunha tesela XYZ en EPSG:3857 (minx, miny, maxx, maxy)."""
    lado = 2 * _MUNDO / 2 ** z
    return (-_MUNDO + x * lado, _MUNDO - (y + 1) * lado, -_MUNDO + (x + 1) * lado,
            _MUNDO - y * lado)


def tesela_do_punto(lat: float, lon: float, z: int) -> tuple[int, int]:
    n = 2 ** z
    x = int((lon + 180) / 360 * n)
    lat_r = math.radians(lat)
    y = int((1 - math.asinh(math.tan(lat_r)) / math.pi) / 2 * n)
    return min(max(x, 0), n - 1), min(max(y, 0), n - 1)


def url_orixe(capa: str, z: int, x: int, y: int) -> str:
    url, _ = ORIXES[capa]
    bbox = ",".join(f"{v:.3f}" for v in bbox_tesela(z, x, y))
    return url.format(z=z, x=x, y=y, bbox=bbox)


def _descargar(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=_ESPERA_S) as resposta:
            datos: bytes = resposta.read()
            tipo = resposta.headers.get("Content-Type", "")
    except OSError:
        return None
    # Os WMS devolven XML cando hai un erro: iso non se garda
    return datos if tipo.startswith("image/") else None


def tesela(capa: str, z: int, x: int, y: int,
           descargar: Callable[[str], bytes | None] = _descargar) -> tuple[bytes, str] | None:
    """A tesela (bytes, tipo MIME): do disco ou, se non está, descargada e gardada."""
    if capa not in ORIXES or not 0 <= z <= 21:
        return None
    _, ext = ORIXES[capa]
    ruta = cartafol_teselas() / capa / str(z) / str(x) / f"{y}.{ext}"
    mime = "image/jpeg" if ext == "jpg" else "image/png"
    if ruta.is_file():
        return ruta.read_bytes(), mime
    datos = descargar(url_orixe(capa, z, x, y))
    if datos is None:
        return None
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_bytes(datos)
    return datos, mime


def teselas_da_zona(lat_min: float, lon_min: float, lat_max: float, lon_max: float,
                    zooms: range = ZOOMS_ZONA) -> list[tuple[int, int, int]]:
    teselas = []
    for z in zooms:
        x0, y0 = tesela_do_punto(lat_max, lon_min, z)
        x1, y1 = tesela_do_punto(lat_min, lon_max, z)
        teselas += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    return teselas


def gardar_zona(puntos: list[tuple[float, float]], capas: tuple[str, ...],
                marxe_m: float = 300,
                descargar: Callable[[str], bytes | None] = _descargar) -> tuple[int, int]:
    """Descarga as teselas arredor dos puntos (parcelas). Devolve (gardadas, fallidas)."""
    if not puntos:
        return 0, 0
    marxe_lat = marxe_m / 111_320
    lat_media = sum(p[0] for p in puntos) / len(puntos)
    marxe_lon = marxe_m / (111_320 * math.cos(math.radians(lat_media)))
    zona = teselas_da_zona(min(p[0] for p in puntos) - marxe_lat,
                           min(p[1] for p in puntos) - marxe_lon,
                           max(p[0] for p in puntos) + marxe_lat,
                           max(p[1] for p in puntos) + marxe_lon)
    if len(zona) * len(capas) > MAXIMO_TESELAS:
        raise ValueError("A zona é demasiado grande para gardala dunha vez")
    gardadas = fallidas = 0
    for capa in capas:
        for z, x, y in zona:
            if tesela(capa, z, x, y, descargar) is None:
                fallidas += 1
            else:
                gardadas += 1
    return gardadas, fallidas
