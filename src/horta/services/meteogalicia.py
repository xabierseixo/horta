"""Servizos web de MeteoGalicia (JSON, sen clave): estacións, datos diarios e predición por
concello. Só se consulta ao abrir unha
pantalla ou ao apuntar un traballo: nada corre de fondo neste ordenador."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

from horta.idiomas import N_

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
    "TS_AVG_-0.1m": "t_chan",
    "HFRIO7_RECUENTO_1.5m": "horas_frio",
    "HSOL_SUM_1.5m": "horas_sol",
    "BH_SUM_1.5m": "balance_hidrico",
}
_SEN_DATO = -9999
# Estado do ceo (JSON_Pred_Concello, anexo II): 1xx de día e 2xx de noite, co mesmo texto
CEO = {1: N_("Despexado"), 2: N_("Nubes altas"), 3: N_("Nubes e claros"), 4: N_("Nubrado"),
       5: N_("Moi nubrado"), 6: N_("Néboas"), 7: N_("Chuvascos"), 8: N_("Nubrado e chuvascos"),
       9: N_("Chuvascos e neve"), 10: N_("Orballo"), 11: N_("Choiva"), 12: N_("Neve"),
       13: N_("Treboada"), 14: N_("Brétema"), 15: N_("Bancos de néboa"), 16: N_("Nubes medias"),
       17: N_("Choiva débil"), 18: N_("Chuvascos débiles"), 19: N_("Treboada con poucas nubes"),
       20: N_("Auga neve"), 21: N_("Sarabia"), 22: N_("Anubrado con chuvascos débiles"),
       23: N_("Anubrado con neve"), 24: N_("Calima"), 25: N_("Cuberto")}
# Vento (anexo III): 299 calma, 300 variable; 301–332 forza × dirección
_FORZAS = ("frouxo", "moderado", "forte", "moi forte")
_DIRECCIONS = ("Norte", "Nordés", "Leste", "Sueste", "Sur", "Sudoeste", "Oeste", "Noroeste")
# Avisos (JSON_Pred_AvisoConcello, anexo II e niveis)
NIVEIS_AVISO = {1: N_("amarelo"), 2: N_("laranxa"), 3: N_("vermello")}


def ceo_texto(codigo: int | None) -> str | None:
    return CEO.get(codigo % 100) if codigo and codigo > 0 else None


def vento_texto(codigo: int | None) -> str | None:
    if codigo == 299:
        return "Calma"
    if codigo == 300:
        return "Vento variable"
    if codigo is None or not 301 <= codigo <= 332:
        return None
    forza, direccion = divmod(codigo - 301, 8)
    return f"Vento {_FORZAS[forza]} do {_DIRECCIONS[direccion]}"


def _valor(valor: Any) -> Any:
    return None if valor == _SEN_DATO else valor
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
    ceo: str | None = None
    vento: str | None = None
    uv: int | None = None
    ceo_codigo: int | None = None


@dataclass(frozen=True)
class Aviso:
    """Aviso de MeteoGalicia para un concello (nivel 1 amarelo, 2 laranxa, 3 vermello)."""

    inicio: datetime
    fin: datetime
    nivel: int
    tipo: str


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
        vento = dia.get("vento") or {}
        dias.append(DiaPredicion(
            datetime.fromisoformat(dia["dataPredicion"]).date(), _valor(dia.get("tMin")),
            _valor(dia.get("tMax")), max(choiva) if choiva else None, dia.get("nivelAviso"),
            ceo_texto(_valor(dia.get("ceoDia"))),
            vento_texto(_valor(vento.get("tarde") or vento.get("manha"))),
            _valor(dia.get("uvMax")), _valor(dia.get("ceoDia"))))
    return dias


def ler_avisos(datos: dict[str, Any]) -> list[Aviso]:
    return sorted((Aviso(datetime.fromisoformat(a["dataIni"]), datetime.fromisoformat(a["dataFin"]),
                         a["idNivel"], a.get("tipoalerta_gl") or "")
                   for dia in datos.get("listaDiaConcellos") or []
                   for a in dia.get("listaAvisosConcellos") or []
                   if a.get("idNivel") in NIVEIS_AVISO), key=lambda a: a.inicio)


class Fonte(Protocol):
    """De onde vén o tempo. Nas probas, un exemplo gardado; na app, MeteoGalicia."""

    def estacions(self) -> list[Estacion]: ...

    def dias(self, estacion_id: int, desde: date, ata: date) -> list[Dia]: ...

    def predicion(self, concello_ine: str) -> list[DiaPredicion]: ...

    def avisos(self, concello_ine: str) -> list[Aviso]: ...


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

    def avisos(self, concello_ine: str) -> list[Aviso]:
        return ler_avisos(self._ler(
            f"predicion/adversos/jsonAvisosConcellos.action?idConcello={int(concello_ine)}"
            "&dia=-1"))
