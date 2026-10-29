"""O tempo de cada traballo e de cada lugar:
concellos (INE), estacións de MeteoGalicia, o tempo dun día e os avisos. Os avisos nunca
bloquean."""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.db import Base
from horta.models.horta import Horta, RolHorta
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
from horta.models.tempo import EstacionMeteo, TempoDia, ligar_tempo, onde_e_cando
from horta.models.traballo import ParteComun
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.meteogalicia import FONTE, DiaPredicion, Estacion, Fonte, SenTempo

# Guías de extensión agraria: para decidir no campo, a estación a menos de ~10 km
#
LONXE_KM = 10.0
# Boas prácticas: non tratar con vento de máis de 3 m/s (Junta de Andalucía, guía de
# contaminación difusa 2021)
VENTO_DERIVA_MS = 3.0
_CONCELLOS = Path(__file__).resolve().parents[1] / "data" / "concellos_galicia.csv"
# Días que se miran cara atrás ao encher o tempo que falta
DIAS_ATRAS = 365


@cache
def concellos() -> dict[str, str]:
    """Os concellos de Galicia (código INE → nome), da relación oficial do INE (2026)."""
    with _CONCELLOS.open(encoding="utf-8") as ficheiro:
        return {fila["codigo_ine"]: fila["nome"] for fila in csv.DictReader(ficheiro)}


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia sobre a Terra (fórmula do haverseno)."""
    f1, f2 = math.radians(lat1), math.radians(lat2)
    df, dl = f2 - f1, math.radians(lon2 - lon1)
    a = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def por_distancia(estacions: list[Estacion], lat: float, lon: float
                  ) -> list[tuple[Estacion, float]]:
    """As estacións da máis próxima á máis lonxana, coa distancia en km."""
    return sorted(((e, distancia_km(lat, lon, e.lat, e.lon)) for e in estacions),
                  key=lambda par: par[1])


def gardar_lugar(session: Session, actor: Usuario, sitio: Horta | Parcela,
                 concello_ine: str | None, estacion: Estacion | None) -> None:
    """O concello e a estación da explotación ou dunha parcela (baleiros na parcela: os da
    explotación). A estación gárdase para mostrala e medir distancias sen conexión."""
    horta_id = sitio.id if isinstance(sitio, Horta) else sitio.horta_id
    comprobar_rol_horta(session, horta_id, actor,
                        {RolHorta.ADMIN} if isinstance(sitio, Horta)
                        else {RolHorta.ADMIN, RolHorta.EDITOR})
    if concello_ine is not None and concello_ine not in concellos():
        raise OperacionNonPermitidaError("Ese concello non está na lista de Galicia")
    if estacion is not None:
        gardada = session.get(EstacionMeteo, estacion.id) or EstacionMeteo(id=estacion.id)
        gardada.nome, gardada.concello = estacion.nome, estacion.concello
        gardada.lat, gardada.lon, gardada.altitude = estacion.lat, estacion.lon, estacion.altitude
        session.add(gardada)
        # Sen relationship entre as táboas: a estación vai á BD antes de apuntala
        session.flush()
    sitio.concello_ine = concello_ine
    sitio.estacion_meteo_id = estacion.id if estacion else None
    session.commit()


def aviso_distancia(estacion: EstacionMeteo | None, lat: float | None, lon: float | None
                    ) -> str | None:
    if estacion is None or lat is None or lon is None:
        return None
    km = distancia_km(lat, lon, estacion.lat, estacion.lon)
    if km <= LONXE_KM:
        return None
    return (f"A estación está a {km:.0f} km: o tempo pode ser distinto. Escolle outra máis "
            "próxima se a hai")


def _gardar_dia(session: Session, estacion_id: int, data: date,
                medidas: dict[str, float | None]) -> TempoDia:
    tempo = TempoDia(estacion_id=estacion_id, data=data, fonte=FONTE, **medidas)
    session.add(tempo)
    session.flush()
    return tempo


def consultar_dias(session: Session, fonte: Fonte, estacion_id: int, desde: date, ata: date,
                   hoxe: date | None = None) -> dict[date, TempoDia]:
    """O tempo dos días rematados entre dúas datas nunha estación: o gardado e, o que falte,
    de MeteoGalicia nunha soa consulta (e gárdase). Sen conexión, só o gardado."""
    ata = min(ata, (hoxe or date.today()) - timedelta(days=1))
    if ata < desde or session.get(EstacionMeteo, estacion_id) is None:
        return {}
    gardados = {t.data: t for t in session.query(TempoDia).filter(
        TempoDia.estacion_id == estacion_id, TempoDia.data >= desde, TempoDia.data <= ata)}
    faltan = [desde + timedelta(days=n) for n in range((ata - desde).days + 1)
              if desde + timedelta(days=n) not in gardados]
    if faltan:
        try:
            dias = fonte.dias(estacion_id, faltan[0], faltan[-1])
        except SenTempo:
            dias = []
        for dia in dias:
            if dia.estacion_id == estacion_id and dia.data in faltan \
                    and dia.data not in gardados:
                gardados[dia.data] = _gardar_dia(session, estacion_id, dia.data, dia.medidas)
        session.commit()
    return gardados


def consultar_tempo(session: Session, fonte: Fonte, estacion_id: int, data: date,
                    hoxe: date | None = None) -> TempoDia | None:
    """O tempo dun día rematado nunha estación: o gardado ou, se non o hai, de MeteoGalicia
    (e gárdase). None se o día non rematou ou se non hai conexión."""
    return consultar_dias(session, fonte, estacion_id, data, data, hoxe).get(data)


def horas_frio(session: Session, fonte: Fonte, estacion_id: int | None,
               hoxe: date | None = None) -> float | None:
    """Horas a 7 ºC ou menos desde o 1 de novembro (o que piden os froiteiros para
    florecer ben). Só de novembro a marzo."""
    hoxe = hoxe or date.today()
    if estacion_id is None or hoxe.month not in (11, 12, 1, 2, 3):
        return None
    inicio = date(hoxe.year if hoxe.month >= 11 else hoxe.year - 1, 11, 1)
    dias = consultar_dias(session, fonte, estacion_id, inicio, hoxe, hoxe)
    horas = [t.horas_frio for t in dias.values() if t.horas_frio is not None]
    return sum(horas) if horas else None


def _modelos_con_parte_comun() -> list[type[Any]]:
    return [m.class_ for m in Base.registry.mappers if issubclass(m.class_, ParteComun)]


def encher_tempo(session: Session, actor: Usuario, horta_id: int, fonte: Fonte,
                 hoxe: date | None = None) -> int:
    """Enche o tempo dos traballos que non o teñen (sen conexión ao apuntalos, ou do día en
    curso). Unha consulta por estación para todos os días que faltan. Devolve cantos."""
    comprobar_rol_horta(session, horta_id, actor,
                        {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR})
    hoxe = hoxe or date.today()
    desde = hoxe - timedelta(days=DIAS_ATRAS)
    sen_tempo: dict[int, list[tuple[object, date]]] = defaultdict(list)
    for modelo in _modelos_con_parte_comun():
        for traballo in session.query(modelo).filter_by(tempo_id=None, baixa=False):
            horta, estacion_id, data = onde_e_cando(session, traballo)
            if horta == horta_id and estacion_id is not None and data is not None \
                    and desde <= data < hoxe:
                sen_tempo[estacion_id].append((traballo, data))
    enchidos = 0
    for estacion_id, traballos in sen_tempo.items():
        datas = {data for _, data in traballos}
        gardados = {t.data for t in session.query(TempoDia).filter(
            TempoDia.estacion_id == estacion_id, TempoDia.data.in_(datas))}
        faltan = datas - gardados
        if faltan:
            try:
                dias = fonte.dias(estacion_id, min(faltan), max(faltan))
            except SenTempo:
                continue
            for dia in dias:
                if dia.estacion_id == estacion_id and dia.data in faltan:
                    _gardar_dia(session, estacion_id, dia.data, dia.medidas)
        for sen, _ in traballos:
            ligar_tempo(session, sen)
            enchidos += getattr(sen, "tempo_id") is not None
    session.commit()
    return enchidos


@dataclass(frozen=True)
class TempoDoTraballo:
    """O tempo para mostrar nun formulario: o resumo e os avisos."""

    resumo: str
    avisos: list[str]
    info: list[str] = field(default_factory=list)


def _n(valor: float | None, unidade: str) -> str:
    return "?" if valor is None else f"{valor:.1f}".rstrip("0").rstrip(".") + unidade


def resumo(tempo: TempoDia, estacion: str) -> str:
    return (f"{estacion}, {tempo.data:%d/%m}: {_n(tempo.t_min, '')}–{_n(tempo.t_max, ' ºC')}, "
            f"{_n(tempo.choiva, ' l/m²')}, vento {_n(tempo.vento_medio, ' m/s')} "
            f"(refacho {_n(tempo.refacho, '')}), humidade {_n(tempo.humidade, ' %')}, "
            f"chan {_n(tempo.t_chan, ' ºC')}")


def avisos(tipo: str, tempo: TempoDia, choiva_antes: float | None = None) -> list[str]:
    """Os avisos do tempo dun traballo (tipos do Diario). Nunca bloquean."""
    lista: list[str] = []
    choveu = tempo.choiva is not None and tempo.choiva > 0
    if tipo == "abonado":
        if choveu:
            lista.append(f"Choveu {_n(tempo.choiva, ' l/m²')} ese día: non se pode abonar en "
                         "terreo encharcado ou inundado (RD 1051/2022, art. 4.4)")
        if tempo.t_min is not None and tempo.t_min <= 0:
            lista.append("Xeou ese día: non se pode abonar en terreo xeado "
                         "(RD 1051/2022, art. 4.4)")
    elif tipo == "tratamento":
        if choveu:
            lista.append(f"Choveu {_n(tempo.choiva, ' l/m²')} ese día: o produto pode lavarse. "
                         "Mira a etiqueta")
        if tempo.vento_medio is not None and tempo.vento_medio > VENTO_DERIVA_MS:
            lista.append(f"Vento medio de {_n(tempo.vento_medio, ' m/s')} ese día: risco de "
                         "deriva. É a media do día, non da hora do tratamento")
    elif tipo == "rega" and choiva_antes:
        lista.append(f"Choveron {_n(choiva_antes, ' l/m²')} nos dous días anteriores")
    return lista


def tempo_do_traballo(session: Session, fonte: Fonte, tipo: str, estacion_id: int | None,
                      data: date | None, hoxe: date | None = None) -> TempoDoTraballo | None:
    """O tempo dese día na estación, para mostralo no formulario mentres se apunta."""
    if estacion_id is None or data is None:
        return None
    # Na rega mírase a semana enteira: unha soa consulta
    semana = (consultar_dias(session, fonte, estacion_id, data - timedelta(days=6), data, hoxe)
              if tipo == "rega" else {})
    tempo = semana.get(data) if tipo == "rega" else consultar_tempo(session, fonte, estacion_id,
                                                                     data, hoxe)
    estacion = session.get(EstacionMeteo, estacion_id)
    if tempo is None or estacion is None:
        return None
    choiva_antes = None
    info: list[str] = []
    if tipo == "rega":
        choiva_antes = sum(semana[d].choiva or 0 for d in
                           (data - timedelta(days=1), data - timedelta(days=2)) if d in semana)
        if tempo.et0 is not None:
            info.append(f"Evapotranspiración ese día: {_n(tempo.et0, ' l/m²')} (a auga que "
                        "perden o chan e as plantas)")
        balance = [t.balance_hidrico for t in semana.values() if t.balance_hidrico is not None]
        if balance:
            info.append(f"Balance hídrico dos 7 días: {_n(sum(balance), ' l/m²')} "
                        "(negativo: falta auga)")
    return TempoDoTraballo(resumo(tempo, estacion.nome), avisos(tipo, tempo, choiva_antes),
                           info)


def estacion_do_lugar(session: Session, horta_id: int, parcela_id: int | None) -> int | None:
    """A estación dunha parcela ou, sen ela, a da explotación."""
    parcela = session.get(Parcela, parcela_id) if parcela_id is not None else None
    horta = session.get(Horta, horta_id)
    return ((parcela.estacion_meteo_id if parcela else None)
            or (horta.estacion_meteo_id if horta else None))


# Predición (paso 9b): non se garda, consúltase ao abrir Inicio
CHOIVA_PREVISTA_PCT = 70  # deseño do tempo: aviso nas tarefas de tratamento


def avisos_tarefas(tarefas: list[Tarefa], predicion: list[DiaPredicion]) -> list[str]:
    """As tarefas de tratamento por facer nun día con choiva prevista. Nunca bloquean."""
    por_dia = {d.data: d for d in predicion}
    avisos_: list[str] = []
    for tarefa in tarefas:
        dia = por_dia.get(tarefa.data) if tarefa.data else None
        if (tarefa.tipo == "tratamento" and tarefa.estado != "feito" and dia is not None
                and dia.choiva_pct is not None and dia.choiva_pct >= CHOIVA_PREVISTA_PCT):
            avisos_.append(f"«{tarefa.descricion}» o {dia.data:%d/%m}: probabilidade de choiva "
                           f"do {dia.choiva_pct} %")
    return avisos_
