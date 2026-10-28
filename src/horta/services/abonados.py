"""Abonados dos cultivos (CUE bloque 9, fertilización). Un cultivo por abonado. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes import UNIDADES_DOSE, nutrientes_kg_ha
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Boa práctica "Abonado en verde": é a única que permite non indicar abono (CUE)
ABONADO_EN_VERDE = "20"


@dataclass
class DatosAbonado:
    cultivo_id: int
    data_inicio: date
    tipo_fertilizacion: str | None = None
    metodo: str | None = None
    boas_practicas: list[str] = field(default_factory=list)
    fertilizante_id: int | None = None
    dose: float | None = None
    unidade: str | None = None
    data_fin: date | None = None
    superficie_ha: float | None = None
    xestion_sostible: bool = False
    aplicacion_lodos: bool = False
    albaran_factura: str | None = None
    persoa_id: int | None = None
    horas: float | None = None
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h_ha: float | None = None
    notas: str | None = None


def _horta_do_cultivo(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    return cultivo, horta_id


def _validar(
    session: Session, datos: DatosAbonado, cultivo: Cultivo, horta_id: int, hoxe: date
) -> None:
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data do abonado non pode ser futura")
    # Quen o fixo pode ser unha persoa do equipo ou a empresa de servizos (co seu REGFER)
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie abonada é maior ca do cultivo")
    if datos.tipo_fertilizacion:
        validar_codigo(session, "tipo_fertilizacion", datos.tipo_fertilizacion, datos.data_inicio)
    if datos.metodo:
        validar_codigo(session, "metodo_fertilizacion", datos.metodo, datos.data_inicio)
    for codigo in datos.boas_practicas:
        valor = validar_codigo(session, "boas_practicas", codigo, datos.data_inicio)
        if "fertilizacion" not in (valor.categoria or ""):
            raise OperacionNonPermitidaError(f"A boa práctica {codigo} non é de fertilización")
    if datos.fertilizante_id is None:
        if ABONADO_EN_VERDE not in datos.boas_practicas:
            raise OperacionNonPermitidaError("Escolle o abono")
        return
    fertilizante = session.get(Fertilizante, datos.fertilizante_id)
    if fertilizante is None or fertilizante.horta_id != horta_id:
        raise OperacionNonPermitidaError("Ese abono non é desta explotación")
    if datos.dose is None:
        return
    if datos.dose <= 0:
        raise OperacionNonPermitidaError("A dose ten que ser maior que 0")
    if datos.unidade not in UNIDADES_DOSE:
        raise OperacionNonPermitidaError("Escolle a unidade da dose (por hectárea ou por m²)")


def _copiar(abonado: Abonado, datos: DatosAbonado, horta_id: int, cultivo: Cultivo) -> None:
    abonado.horta_id = horta_id
    abonado.cultivo_id = datos.cultivo_id
    abonado.data_inicio = datos.data_inicio
    abonado.data_fin = datos.data_fin or datos.data_inicio
    abonado.superficie_ha = datos.superficie_ha or cultivo.superficie_ha
    abonado.fertilizante_id = datos.fertilizante_id
    abonado.dose = datos.dose if datos.fertilizante_id else None
    abonado.unidade = datos.unidade if datos.fertilizante_id and datos.dose else None
    abonado.tipo_fertilizacion = datos.tipo_fertilizacion or None
    abonado.metodo = datos.metodo or None
    abonado.xestion_sostible = datos.xestion_sostible
    abonado.aplicacion_lodos = datos.aplicacion_lodos
    abonado.albaran_factura = datos.albaran_factura or None
    abonado.persoa_id = datos.persoa_id
    abonado.horas = datos.horas
    abonado.maquina_id = datos.maquina_id
    abonado.num_repeticions = datos.num_repeticions
    abonado.duracion_h_ha = datos.duracion_h_ha
    abonado.notas = datos.notas or None
    abonado.boas_practicas = [AbonadoBoaPractica(codigo=c) for c in datos.boas_practicas]


def crear_abonado(
    session: Session, actor: Usuario, datos: DatosAbonado, hoxe: date | None = None
) -> Abonado:
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    abonado = Abonado(creado_por=actor.id)
    _copiar(abonado, datos, horta_id, cultivo)
    session.add(abonado)
    session.commit()
    return abonado


def actualizar_abonado(
    session: Session, actor: Usuario, abonado: Abonado, datos: DatosAbonado,
    hoxe: date | None = None,
) -> Abonado:
    if abonado.baixa:
        raise OperacionNonPermitidaError("Un abonado dado de baixa non se pode modificar")
    comprobar_rol_horta(session, abonado.horta_id, actor, _ROLES_ESCRITURA)
    cultivo, horta_id = _horta_do_cultivo(session, datos.cultivo_id)
    if horta_id != abonado.horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    _copiar(abonado, datos, horta_id, cultivo)
    session.commit()
    return abonado


def dar_de_baixa_abonado(session: Session, actor: Usuario, abonado: Abonado) -> None:
    comprobar_rol_horta(session, abonado.horta_id, actor, _ROLES_ESCRITURA)
    abonado.baixa = True
    session.commit()


def listar_abonados(
    session: Session, actor: Usuario, horta_id: int, cultivo_id: int | None = None
) -> list[Abonado]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Abonado).filter_by(horta_id=horta_id, baixa=False)
    if cultivo_id is not None:
        consulta = consulta.filter_by(cultivo_id=cultivo_id)
    return list(consulta.order_by(Abonado.data_inicio.desc(), Abonado.id.desc()))


def nutrientes_do_abonado(session: Session, abonado: Abonado) -> tuple[float, float, float] | None:
    """kg/ha de N, P₂O₅ e K₂O deste abonado; None sen abono, dose ou densidade."""
    if abonado.fertilizante_id is None or abonado.dose is None or abonado.unidade is None:
        return None
    fertilizante = session.get(Fertilizante, abonado.fertilizante_id)
    return nutrientes_kg_ha(fertilizante, abonado.dose, abonado.unidade) if fertilizante else None
