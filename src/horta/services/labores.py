"""Labores culturais dos cultivos (CUE bloque 5). Un cultivo por labor. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.labor import Labor
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo TIPO_LABOR: onde o CUE pregunta se os restos quedaron no chan
DESBROCE = "5"
PODAS = ("7", "11", "12")


@dataclass
class DatosLabor:
    cultivo_id: int
    data_inicio: date
    tipo_labor: str
    data_fin: date | None = None
    superficie_ha: float | None = None
    restos_desbroce_no_solo: bool = False
    restos_poda_no_solo: bool = False
    tipo_cobertura: str | None = None
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h: float | None = None
    persoa_id: int | None = None
    notas: str | None = None


def _cultivo_e_parcela(session: Session, cultivo_id: int) -> tuple[Cultivo, Parcela]:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    return cultivo, parcela


def _validar(session: Session, datos: DatosLabor, cultivo: Cultivo, horta_id: int,
             hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do labor non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie do labor é maior ca do cultivo")
    for valor, texto in ((datos.num_repeticions, "repeticións"), (datos.duracion_h, "horas")):
        if valor is not None and valor <= 0:
            raise OperacionNonPermitidaError(f"O número de {texto} ten que ser maior que 0")
    validar_codigo(session, "tipo_labor", datos.tipo_labor, datos.data_inicio)
    if datos.tipo_cobertura:
        validar_codigo(session, "tipo_cobertura_solo", datos.tipo_cobertura, datos.data_inicio)
    if datos.maquina_id is not None:
        maquina = session.get(Maquina, datos.maquina_id)
        if maquina is None or maquina.horta_id != horta_id:
            raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
    if datos.persoa_id is not None:
        persoa = session.get(Persoa, datos.persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")


def _copiar(labor: Labor, datos: DatosLabor, cultivo: Cultivo, parcela: Parcela) -> None:
    labor.horta_id = parcela.horta_id
    labor.cultivo_id = datos.cultivo_id
    labor.data_inicio = datos.data_inicio
    labor.data_fin = datos.data_fin or datos.data_inicio
    labor.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    labor.tipo_labor = datos.tipo_labor
    # Os restos só se anotan nos labores onde o CUE os pregunta
    labor.restos_desbroce_no_solo = datos.tipo_labor == DESBROCE and datos.restos_desbroce_no_solo
    labor.restos_poda_no_solo = datos.tipo_labor in PODAS and datos.restos_poda_no_solo
    labor.tipo_cobertura = datos.tipo_cobertura or cultivo.tipo_cobertura_solo
    labor.maquina_id = datos.maquina_id
    labor.num_repeticions = datos.num_repeticions
    labor.duracion_h = datos.duracion_h
    labor.persoa_id = datos.persoa_id
    labor.notas = datos.notas or None


def crear_labor(
    session: Session, actor: Usuario, datos: DatosLabor, hoxe: date | None = None
) -> Labor:
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, parcela.horta_id, hoxe or date.today())
    labor = Labor(creado_por=actor.id)
    _copiar(labor, datos, cultivo, parcela)
    session.add(labor)
    session.commit()
    return labor


def actualizar_labor(
    session: Session, actor: Usuario, labor: Labor, datos: DatosLabor, hoxe: date | None = None
) -> Labor:
    if labor.baixa:
        raise OperacionNonPermitidaError("Un labor dado de baixa non se pode modificar")
    comprobar_rol_horta(session, labor.horta_id, actor, _ROLES_ESCRITURA)
    cultivo, parcela = _cultivo_e_parcela(session, datos.cultivo_id)
    if parcela.horta_id != labor.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, labor.horta_id, hoxe or date.today())
    _copiar(labor, datos, cultivo, parcela)
    session.commit()
    return labor


def dar_de_baixa_labor(session: Session, actor: Usuario, labor: Labor) -> None:
    comprobar_rol_horta(session, labor.horta_id, actor, _ROLES_ESCRITURA)
    labor.baixa = True
    session.commit()


def listar_labores(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Labor]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Labor).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Labor.data_inicio.desc(), Labor.id.desc()))


def ultimo_labor(session: Session, cultivo_id: int) -> str | None:
    """O tipo do último labor dese cultivo, para propoñelo no seguinte."""
    labor = (session.query(Labor).filter_by(cultivo_id=cultivo_id, baixa=False)
             .order_by(Labor.data_inicio.desc(), Labor.id.desc()).first())
    return labor.tipo_labor if labor else None
