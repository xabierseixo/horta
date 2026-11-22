"""Regas dos cultivos (CUE bloque 10). Un cultivo por rega. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.rega import Rega, RegaBoaPractica, RegaCultivo
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.leiras import LeiraTraballo, LeiraValida, as_leiras, validar_leiras
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo UNIDADES_MEDIDA: m³ e litros
UNIDADES_AUGA = ("3", "4")


@dataclass(kw_only=True)
class DatosRega:
    data_inicio: date
    # As leiras; ou, para unha soa, cultivo_id e superficie_ha. A auga é a total
    leiras: list[LeiraTraballo] = field(default_factory=list)
    cultivo_id: int | None = None
    sistema_rega: str | None = None
    cantidade: float | None = None
    unidade: str = "4"
    data_fin: date | None = None
    superficie_ha: float | None = None
    orixe_auga: str | None = None
    tipo_enerxia: str | None = None
    num_contador: str | None = None
    persoa_id: int | None = None
    horas: float | None = None
    maquina_id: int | None = None
    boas_practicas: list[str] = field(default_factory=list)
    notas: str | None = None


def _validar(session: Session, datos: DatosRega, horta_id: int, hoxe: date) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data da rega non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, horta_id, datos.maquina_id)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.cantidade is not None and datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade de auga ten que ser maior que 0")
    if datos.unidade not in UNIDADES_AUGA:
        raise OperacionNonPermitidaError("A auga vai en litros ou m³")
    if datos.sistema_rega:
        validar_codigo(session, "sistema_rega", datos.sistema_rega, datos.data_inicio)
    if datos.orixe_auga:
        validar_codigo(session, "orixe_auga", datos.orixe_auga, datos.data_inicio)
    if datos.tipo_enerxia:
        validar_codigo(session, "tipo_enerxia", datos.tipo_enerxia, datos.data_inicio)
    for codigo in datos.boas_practicas:
        valor = validar_codigo(session, "boas_practicas", codigo, datos.data_inicio)
        if "rega" not in (valor.categoria or ""):
            raise OperacionNonPermitidaError(f"A boa práctica {codigo} non é de rega")


def _copiar(rega: Rega, datos: DatosRega, horta_id: int, leiras: list[LeiraValida]) -> None:
    rega.horta_id = horta_id
    rega.leiras = [RegaCultivo(cultivo_id=le.cultivo.id, superficie_ha=le.superficie_ha)
                   for le in leiras]
    rega.data_inicio = datos.data_inicio
    rega.data_fin = datos.data_fin or datos.data_inicio
    rega.sistema_rega = datos.sistema_rega or None
    rega.cantidade = datos.cantidade
    rega.unidade = datos.unidade
    rega.orixe_auga = datos.orixe_auga or leiras[0].parcela.orixe_auga
    rega.tipo_enerxia = datos.tipo_enerxia or None
    rega.num_contador = datos.num_contador or None
    rega.persoa_id = datos.persoa_id
    rega.horas = datos.horas
    rega.maquina_id = datos.maquina_id
    rega.notas = datos.notas or None
    rega.boas_practicas = [RegaBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_rega(
    session: Session, actor: Usuario, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    horta_id, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras))
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, horta_id, hoxe or date.today())
    rega = Rega(creado_por=actor.id)
    _copiar(rega, datos, horta_id, leiras)
    session.add(rega)
    session.commit()
    return rega


def actualizar_rega(
    session: Session, actor: Usuario, rega: Rega, datos: DatosRega, hoxe: date | None = None
) -> Rega:
    if rega.baixa:
        raise OperacionNonPermitidaError("Unha rega dada de baixa non se pode modificar")
    comprobar_rol_horta(session, rega.horta_id, actor, _ROLES_ESCRITURA)
    _, leiras = validar_leiras(
        session, as_leiras(datos.cultivo_id, datos.superficie_ha, datos.leiras), rega.horta_id)
    _validar(session, datos, rega.horta_id, hoxe or date.today())
    _copiar(rega, datos, rega.horta_id, leiras)
    session.commit()
    return rega


def dar_de_baixa_rega(session: Session, actor: Usuario, rega: Rega) -> None:
    comprobar_rol_horta(session, rega.horta_id, actor, _ROLES_ESCRITURA)
    rega.baixa = True
    session.commit()


def listar_regas(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Rega]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Rega).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter(Rega.leiras.any(RegaCultivo.cultivo_id == cultivo_id))
    return list(consulta.order_by(Rega.data_inicio.desc(), Rega.id.desc()))


def ultimo_sistema_rega(session: Session, cultivo_id: int) -> str | None:
    """O sistema de rega da última rega dese cultivo, para propoñelo na seguinte."""
    rega = (session.query(Rega).filter(Rega.baixa.is_(False),
                                       Rega.leiras.any(RegaCultivo.cultivo_id == cultivo_id))
            .order_by(Rega.data_inicio.desc(), Rega.id.desc()).first())
    return rega.sistema_rega if rega else None


def litros_estimados(
    minutos: float | None = None, litros_minuto: float | None = None,
    regadeiras: float | None = None, litros_regadeira: float | None = None,
) -> float | None:
    """Calculadora para quen non sabe os litros: minutos × l/min ou regadeiras × litros."""
    if minutos and litros_minuto:
        return round(minutos * litros_minuto, 1)
    if regadeiras and litros_regadeira:
        return round(regadeiras * litros_regadeira, 1)
    return None
