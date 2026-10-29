"""Outro traballo (mantemento, limpeza, arranxos…): descrición e parte común, nunha parcela,
cuns animais ou na explotación enteira
. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.instalacions import comprobar_instalacion
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass(kw_only=True)
class DatosOutroTraballo:
    horta_id: int
    data_inicio: date
    descricion: str
    data_fin: date | None = None
    parcela_id: int | None = None
    animal_id: int | None = None
    instalacion_id: int | None = None
    persoa_id: int | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def _validar(session: Session, datos: DatosOutroTraballo, hoxe: date) -> None:
    if not datos.descricion.strip():
        raise OperacionNonPermitidaError("Indica que traballo se fixo")
    if datos.data_inicio > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    if datos.data_fin is not None and datos.data_fin < datos.data_inicio:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.parcela_id is not None:
        parcela = session.get(Parcela, datos.parcela_id)
        if parcela is None or parcela.horta_id != datos.horta_id:
            raise OperacionNonPermitidaError("A parcela non é desta explotación")
    if datos.animal_id is not None:
        animal = session.get(Animal, datos.animal_id)
        if animal is None or animal.horta_id != datos.horta_id:
            raise OperacionNonPermitidaError("O grupo de animais non é desta explotación")
    comprobar_instalacion(session, datos.horta_id, datos.instalacion_id)
    comprobar_quen(session, datos.horta_id, datos.persoa_id, datos.horas)
    comprobar_maquina(session, datos.horta_id, datos.maquina_id)


def _copiar(traballo: OutroTraballo, datos: DatosOutroTraballo) -> None:
    traballo.horta_id = datos.horta_id
    traballo.data_inicio = datos.data_inicio
    traballo.data_fin = datos.data_fin or datos.data_inicio
    traballo.descricion = datos.descricion.strip()
    traballo.parcela_id = datos.parcela_id
    traballo.animal_id = datos.animal_id
    traballo.instalacion_id = datos.instalacion_id
    traballo.persoa_id = datos.persoa_id
    traballo.horas = datos.horas
    traballo.maquina_id = datos.maquina_id
    traballo.notas = datos.notas or None


def crear_outro_traballo(
    session: Session, actor: Usuario, datos: DatosOutroTraballo, hoxe: date | None = None
) -> OutroTraballo:
    comprobar_rol_horta(session, datos.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    traballo = OutroTraballo(creado_por=actor.id)
    _copiar(traballo, datos)
    session.add(traballo)
    session.commit()
    return traballo


def actualizar_outro_traballo(
    session: Session, actor: Usuario, traballo: OutroTraballo, datos: DatosOutroTraballo,
    hoxe: date | None = None,
) -> OutroTraballo:
    if traballo.baixa:
        raise OperacionNonPermitidaError("Un traballo dado de baixa non se pode modificar")
    if datos.horta_id != traballo.horta_id:
        raise OperacionNonPermitidaError("O traballo non se pode pasar a outra explotación")
    comprobar_rol_horta(session, traballo.horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, hoxe or date.today())
    _copiar(traballo, datos)
    session.commit()
    return traballo


def dar_de_baixa_outro_traballo(session: Session, actor: Usuario, traballo: OutroTraballo
                                ) -> None:
    comprobar_rol_horta(session, traballo.horta_id, actor, _ROLES_ESCRITURA)
    traballo.baixa = True
    session.commit()


def listar_outros_traballos(session: Session, actor: Usuario, horta_id: int
                            ) -> list[OutroTraballo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(OutroTraballo).filter_by(horta_id=horta_id, baixa=False)
                .order_by(OutroTraballo.data_inicio.desc(), OutroTraballo.id.desc()))
