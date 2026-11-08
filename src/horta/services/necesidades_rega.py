"""Cálculo das necesidades de rega segundo o método FAO-56 (SiAR do MAPA)."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from datetime import date, timedelta
from functools import cache
from pathlib import Path

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.parcela import Parcela
from horta.models.rega import Rega, RegaCultivo
from horta.models.tempo import EstacionMeteo
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.meteogalicia import Fonte, MeteoGalicia
from horta.services.tempo import consultar_dias

_CSV_KC = Path(__file__).resolve().parents[1] / "data" / "kc_fao56.csv"
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

CODIGO_SECANO = "S"
PORCENTAXE_CHOIVA_EFECTIVA = 0.8
FONTE: Fonte = MeteoGalicia()


@dataclass(frozen=True)
class CoeficienteCultivo:
    codigo_siex: int
    nome: str
    cultivo_fao56: str
    kc_ini: float
    kc_mid: float
    kc_end: float
    l_ini: int | None
    l_dev: int | None
    l_mid: int | None
    l_late: int | None
    nota: str


@dataclass(frozen=True)
class NecesidadeRega:
    cultivo_id: int
    estado: str
    etc_mm: float
    choiva_efectiva_mm: float
    rega_mm: float
    falta_mm: float
    kc_actual: float | None
    aproximado: bool
    dias_con_datos: int
    et0_estimada: bool = False


def _parse_int_ou_none(valor: str | None) -> int | None:
    if not valor or not valor.strip():
        return None
    return int(valor.strip())


@cache
def coeficientes() -> dict[int, CoeficienteCultivo]:
    """Le os coeficientes de cultivo FAO-56 do CSV incluído no paquete."""
    resultado: dict[int, CoeficienteCultivo] = {}
    with _CSV_KC.open(encoding="utf-8") as ficheiro:
        lector = csv.DictReader(ficheiro, delimiter=";")
        for fila in lector:
            if not fila or not fila.get("codigo_siex"):
                continue
            codigo = int(fila["codigo_siex"])
            resultado[codigo] = CoeficienteCultivo(
                codigo_siex=codigo,
                nome=fila["nome"].strip(),
                cultivo_fao56=fila["cultivo_fao56"].strip(),
                kc_ini=float(fila["kc_ini"]),
                kc_mid=float(fila["kc_mid"]),
                kc_end=float(fila["kc_end"]),
                l_ini=_parse_int_ou_none(fila.get("l_ini")),
                l_dev=_parse_int_ou_none(fila.get("l_dev")),
                l_mid=_parse_int_ou_none(fila.get("l_mid")),
                l_late=_parse_int_ou_none(fila.get("l_late")),
                nota=fila.get("nota", "").strip(),
            )
    return resultado


def kc_do_dia(coef: CoeficienteCultivo, dias: int) -> float:
    """Calcula o coeficiente Kc para un determinado número de días desde o inicio.

    Segue o método FAO-56 (curva do Kc de catro fases).
    Se falta algún l_*, devolve sempre kc_mid.
    Para días negativos devolve kc_ini.
    Despois do ciclo completo devolve kc_end.
    """
    if (
        coef.l_ini is None
        or coef.l_dev is None
        or coef.l_mid is None
        or coef.l_late is None
    ):
        return coef.kc_mid

    if dias < 0:
        return coef.kc_ini

    if dias < coef.l_ini:
        return coef.kc_ini

    fin_dev = coef.l_ini + coef.l_dev
    if dias < fin_dev:
        if coef.l_dev == 0:
            return coef.kc_mid
        fraccion = (dias - coef.l_ini) / coef.l_dev
        return coef.kc_ini + (coef.kc_mid - coef.kc_ini) * fraccion

    fin_mid = fin_dev + coef.l_mid
    if dias < fin_mid:
        return coef.kc_mid

    fin_late = fin_mid + coef.l_late
    if dias < fin_late:
        if coef.l_late == 0:
            return coef.kc_end
        fraccion = (dias - fin_mid) / coef.l_late
        return coef.kc_mid + (coef.kc_end - coef.kc_mid) * fraccion

    return coef.kc_end


def choiva_efectiva(choiva_mm: float | None) -> float:
    """O 80 % da choiva do día (método de porcentaxe fixa de FAO/CROPWAT). None vale 0."""
    if choiva_mm is None or choiva_mm <= 0:
        return 0.0
    return choiva_mm * PORCENTAXE_CHOIVA_EFECTIVA


def radiacion_extraterrestre(lat_graos: float, dia: date) -> float:
    """Devolve a radiación extraterrestre Ra en MJ m⁻² día⁻¹ (FAO-56, ec. 21–25)."""
    j = dia.timetuple().tm_yday
    dr = 1.0 + 0.033 * math.cos(2.0 * math.pi * j / 365.0)
    delta = 0.409 * math.sin(2.0 * math.pi * j / 365.0 - 1.39)
    phi = math.radians(lat_graos)
    arg_acos = -math.tan(phi) * math.tan(delta)
    arg_acos = max(-1.0, min(1.0, arg_acos))
    omega_s = math.acos(arg_acos)
    ra = (
        (24.0 * 60.0 / math.pi)
        * 0.0820
        * dr
        * (
            omega_s * math.sin(phi) * math.sin(delta)
            + math.cos(phi) * math.cos(delta) * math.sin(omega_s)
        )
    )
    return max(0.0, ra)


def et0_hargreaves(t_min: float, t_max: float, ra: float) -> float:
    """Calcula a evapotranspiración de referencia ET0 pola ecuación de Hargreaves (FAO-56, ec. 52).

    Devolve a ET0 en mm/día. Se t_max < t_min, devolve 0.0.
    """
    if t_max < t_min:
        return 0.0
    t_media = (t_max + t_min) / 2.0
    et0 = 0.0023 * (t_media + 17.8) * math.sqrt(t_max - t_min) * 0.408 * ra
    return max(0.0, et0)


def auga_regada_mm(
    session: Session,
    cultivo: Cultivo | int,
    desde: date,
    ata: date,
) -> float:
    """Calcula os l/m² (mm) regados nun cultivo entre dúas datas (por data_inicio da rega).

    Conta só as regas que non estean de baixa e que inclúan o cultivo nas súas leiras.
    """
    if isinstance(cultivo, int):
        cultivo_obj = session.get(Cultivo, cultivo)
        if cultivo_obj is None:
            raise ValueError("Ese cultivo non existe")
        cultivo = cultivo_obj

    regas = (
        session.query(Rega)
        .join(RegaCultivo, RegaCultivo.rega_id == Rega.id)
        .filter(
            RegaCultivo.cultivo_id == cultivo.id,
            Rega.baixa.is_(False),
            Rega.data_inicio >= desde,
            Rega.data_inicio <= ata,
        )
        .distinct()
        .all()
    )

    total_mm = 0.0
    for rega in regas:
        if rega.cantidade is None or rega.cantidade <= 0:
            continue
        if rega.unidade == "3":
            litros = rega.cantidade * 1000.0
        elif rega.unidade == "4":
            litros = rega.cantidade
        else:
            continue

        suma_ha = 0.0
        for leira in rega.leiras:
            sup = leira.superficie_ha
            if sup is None:
                c = (
                    cultivo
                    if leira.cultivo_id == cultivo.id
                    else session.get(Cultivo, leira.cultivo_id)
                )
                sup = c.superficie_ha if c else None
            if sup is not None and sup > 0:
                suma_ha += sup

        if suma_ha <= 0:
            continue

        superficie_m2 = suma_ha * 10_000.0
        total_mm += litros / superficie_m2

    return total_mm


def necesidade_rega(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    dias: int = 7,
    hoxe: date | None = None,
    fonte: Fonte = FONTE,
) -> NecesidadeRega:
    """Calcula as necesidades de rega dun cultivo para os últimos días rematados."""
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise ValueError("Ese cultivo non existe")

    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)

    # 1. Se o cultivo é de secano -> "secano"
    if (cultivo.sistema_explotacion or "").strip().upper() == CODIGO_SECANO:
        return NecesidadeRega(
            cultivo_id=cultivo_id,
            estado="secano",
            etc_mm=0.0,
            choiva_efectiva_mm=0.0,
            rega_mm=0.0,
            falta_mm=0.0,
            kc_actual=None,
            aproximado=False,
            dias_con_datos=0,
        )

    # 2. Sen fila no CSV -> "sen_coeficiente"
    coefs = coeficientes()
    coef = (
        coefs.get(cultivo.cultivo_siex_codigo)
        if cultivo.cultivo_siex_codigo is not None
        else None
    )
    if coef is None:
        return NecesidadeRega(
            cultivo_id=cultivo_id,
            estado="sen_coeficiente",
            etc_mm=0.0,
            choiva_efectiva_mm=0.0,
            rega_mm=0.0,
            falta_mm=0.0,
            kc_actual=None,
            aproximado=False,
            dias_con_datos=0,
        )

    aproximado = any(
        fase is None for fase in (coef.l_ini, coef.l_dev, coef.l_mid, coef.l_late)
    )

    # 3. Sen data_inicio -> "sen_data_inicio"
    if cultivo.data_inicio is None:
        return NecesidadeRega(
            cultivo_id=cultivo_id,
            estado="sen_data_inicio",
            etc_mm=0.0,
            choiva_efectiva_mm=0.0,
            rega_mm=0.0,
            falta_mm=0.0,
            kc_actual=None,
            aproximado=aproximado,
            dias_con_datos=0,
        )

    # 4. Sen estación (a da parcela ou, se non ten, a da explotación) -> "sen_estacion"
    parcela = session.get(Parcela, cultivo.parcela_id)
    horta = session.get(Horta, horta_id)
    estacion_id = (parcela.estacion_meteo_id if parcela else None) or (
        horta.estacion_meteo_id if horta else None)
    if estacion_id is None:
        return NecesidadeRega(
            cultivo_id=cultivo_id,
            estado="sen_estacion",
            etc_mm=0.0,
            choiva_efectiva_mm=0.0,
            rega_mm=0.0,
            falta_mm=0.0,
            kc_actual=None,
            aproximado=aproximado,
            dias_con_datos=0,
        )

    hoxe_data = hoxe or date.today()
    desde = hoxe_data - timedelta(days=dias)
    ata = hoxe_data - timedelta(days=1)

    tempo_dias = consultar_dias(
        session, fonte, estacion_id, desde, ata, hoxe_data
    )

    estacion = session.get(EstacionMeteo, estacion_id)
    lat_estacion = estacion.lat if estacion is not None else None

    dias_con_datos = 0
    etc_total = 0.0
    choiva_total = 0.0
    et0_estimada = False

    dia_actual = desde
    while dia_actual <= ata:
        tempo = tempo_dias.get(dia_actual)
        if tempo is not None:
            et0_dia: float | None = None
            if tempo.et0 is not None:
                et0_dia = tempo.et0
            elif (
                lat_estacion is not None
                and tempo.t_min is not None
                and tempo.t_max is not None
            ):
                ra = radiacion_extraterrestre(lat_estacion, dia_actual)
                et0_dia = et0_hargreaves(tempo.t_min, tempo.t_max, ra)
                et0_estimada = True

            if et0_dia is not None:
                dias_desde_inicio = (dia_actual - cultivo.data_inicio).days
                kc = kc_do_dia(coef, dias_desde_inicio)
                etc_total += kc * et0_dia
                choiva_total += choiva_efectiva(tempo.choiva)
                dias_con_datos += 1
        dia_actual += timedelta(days=1)

    if dias_con_datos == 0:
        return NecesidadeRega(
            cultivo_id=cultivo_id,
            estado="sen_datos",
            etc_mm=0.0,
            choiva_efectiva_mm=0.0,
            rega_mm=0.0,
            falta_mm=0.0,
            kc_actual=None,
            aproximado=aproximado,
            dias_con_datos=0,
        )

    if et0_estimada:
        aproximado = True

    rega_total = auga_regada_mm(session, cultivo, desde, ata)
    dias_onte = (ata - cultivo.data_inicio).days
    kc_actual = kc_do_dia(coef, dias_onte)

    etc_mm = round(etc_total, 1)
    choiva_efectiva_mm = round(choiva_total, 1)
    rega_mm = round(rega_total, 1)
    falta_total = max(0.0, etc_total - choiva_total - rega_total)
    falta_mm = round(falta_total, 1)

    return NecesidadeRega(
        cultivo_id=cultivo_id,
        estado="ok",
        etc_mm=etc_mm,
        choiva_efectiva_mm=choiva_efectiva_mm,
        rega_mm=rega_mm,
        falta_mm=falta_mm,
        kc_actual=kc_actual,
        aproximado=aproximado,
        dias_con_datos=dias_con_datos,
        et0_estimada=et0_estimada,
    )


def necesidades_horta(
    session: Session,
    actor: Usuario,
    horta_id: int,
    dias: int = 7,
    hoxe: date | None = None,
    fonte: Fonte = FONTE,
) -> list[NecesidadeRega]:
    """Calcula as necesidades de rega para cada cultivo aberto da horta.

    Os cultivos con estado 'ok' van primeiro, ordenados por falta_mm de maior a menor.
    """
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    cultivos = (
        session.query(Cultivo)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id, Cultivo.data_fin.is_(None))
        .all()
    )

    resultado = [
        necesidade_rega(
            session,
            actor,
            c.id,
            dias=dias,
            hoxe=hoxe,
            fonte=fonte,
        )
        for c in cultivos
    ]

    resultado.sort(
        key=lambda n: (0 if n.estado == "ok" else 1, -n.falta_mm, n.cultivo_id)
    )
    return resultado
