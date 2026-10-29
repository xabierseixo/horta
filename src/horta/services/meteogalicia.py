"""Servizos web de MeteoGalicia (JSON, sen clave): estacións, datos diarios e predición por
concello. Só se consulta ao abrir unha
pantalla ou ao apuntar un traballo: nada corre de fondo neste ordenador."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

URL = "https://servizos.meteogalicia.gal/mgrss"
FONTE = "MeteoGalicia"
_ESPERA_S = 10
# Medidas diarias que se gardan (código de MeteoGalicia → campo de TempoDia)
MEDIDAS = {
    "TA_MIN_1.5m": "t_min",
    "TA_MAX_1.5m": "t_max",
    "TA_AVG_1.5m": "t_media",
    "PP_SUM_1.5m": "choiva",
    "VV_AVG_10m": "vento_medio",
    "VV_MAX_10m": "refacho",
    "HR_AVG_1.5m": "humidade",
    "ET0_SUM_1.5m": "et0",
}
_VALIDADO = 1  # lnCodigoValidacion dun dato válido


class SenTempo(Exception):
    """MeteoGalicia non respondeu (sen conexión ou servizo caído)."""


@dataclass(frozen=True)
class Estacion:
    id: int
    nome: str
    concello: str | None
    lat: float
    lon: float
    altitude: float | None


@dataclass(frozen=True)
class Dia:
    """O tempo dun día nunha estación; None nas medidas que faltan ou sen validar."""

    estacion_id: int
    data: date
    medidas: dict[str, float | None]


@dataclass(frozen=True)
class DiaPredicion:
    data: date
    t_min: float | None
    t_max: float | None
    # Probabilidade de choiva (%): a maior da mañá, a tarde e a noite
    choiva_pct: int | None
    nivel_aviso: int | None


def ler_estacions(datos: dict[str, Any]) -> list[Estacion]:
    return [Estacion(e["idEstacion"], e["estacion"], e.get("concello"), e["lat"], e["lon"],
                     e.get("altitude"))
            for e in datos.get("listaEstacionsMeteo") or []]


def ler_dias(datos: dict[str, Any]) -> list[Dia]:
    dias: list[Dia] = []
    for dia in datos.get("listDatosDiarios") or []:
        data = datetime.fromisoformat(dia["data"]).date()
        for estacion in dia.get("listaEstacions") or []:
            medidas: dict[str, float | None] = dict.fromkeys(MEDIDAS.values())
            for medida in estacion.get("listaMedidas") or []:
                campo = MEDIDAS.get(medida.get("codigoParametro"))
                if campo and medida.get("lnCodigoValidacion") == _VALIDADO:
                    medidas[campo] = medida.get("valor")
            dias.append(Dia(estacion["idEstacion"], data, medidas))
    return dias


def ler_predicion(datos: dict[str, Any]) -> list[DiaPredicion]:
    dias: list[DiaPredicion] = []
    for dia in (datos.get("predConcello") or {}).get("listaPredDiaConcello") or []:
        choiva = [v for v in (dia.get("pchoiva") or {}).values() if v is not None and v >= 0]
        dias.append(DiaPredicion(
            datetime.fromisoformat(dia["dataPredicion"]).date(), dia.get("tMin"),
            dia.get("tMax"), max(choiva) if choiva else None, dia.get("nivelAviso")))
    return dias


class Fonte(Protocol):
    """De onde vén o tempo. Nas probas, un exemplo gardado; na app, MeteoGalicia."""

    def estacions(self) -> list[Estacion]: ...

    def dias(self, estacion_id: int, desde: date, ata: date) -> list[Dia]: ...

    def predicion(self, concello_ine: str) -> list[DiaPredicion]: ...


class MeteoGalicia:
    def _ler(self, ruta: str) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(f"{URL}/{ruta}", timeout=_ESPERA_S) as resposta:
                datos: dict[str, Any] = json.load(resposta)
                return datos
        except (OSError, ValueError) as erro:
            raise SenTempo(str(erro)) from erro

    def estacions(self) -> list[Estacion]:
        return ler_estacions(self._ler("observacion/listaEstacionsMeteo.action"))

    def dias(self, estacion_id: int, desde: date, ata: date) -> list[Dia]:
        return ler_dias(self._ler(
            f"observacion/datosDiariosEstacionsMeteo.action?idEst={estacion_id}"
            f"&dataIni={desde:%d/%m/%Y}&dataFin={ata:%d/%m/%Y}"))

    def predicion(self, concello_ine: str) -> list[DiaPredicion]:
        return ler_predicion(self._ler(
            f"predicion/jsonPredConcellos.action?idConc={int(concello_ine)}"))
