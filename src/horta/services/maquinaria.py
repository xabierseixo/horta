from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.maquina import Maquina
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_IDENTIFICADORES = ("num_roma", "num_reganip", "id_equipo_non_inscribible")

CAMPOS_EDITABLES_MAQUINA = frozenset(
    {"alias", "tipo_une", "marca_modelo", "num_roma", "num_reganip", "id_equipo_non_inscribible",
     "propia", "potencia", "unidade_potencia", "tipo_enerxia", "data_ultima_inspeccion", "alugada",
     "activa"}
)


def _validar(datos: dict[str, Any]) -> None:
    if sum(1 for c in _IDENTIFICADORES if datos.get(c)) > 1:
        raise OperacionNonPermitidaError(
            "Indica só un identificador: nº ROMA, nº REGANIP ou identificador do equipo"
        )


def crear_maquina(
    session: Session, actor: Usuario, horta_id: int, alias: str, **campos: Any
) -> Maquina:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(campos)
    maquina = Maquina(horta_id=horta_id, alias=alias, **campos)
    session.add(maquina)
    session.commit()
    return maquina


def actualizar_maquina(
    session: Session, actor: Usuario, maquina: Maquina, **cambios: Any
) -> Maquina:
    non_editables = set(cambios) - CAMPOS_EDITABLES_MAQUINA
    if non_editables:
        raise ValueError(f"Campos non editables nunha máquina: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, maquina.horta_id, actor, _ROLES_ESCRITURA)
    _validar({c: getattr(maquina, c) for c in _IDENTIFICADORES} | cambios)
    for campo, valor in cambios.items():
        setattr(maquina, campo, valor)
    session.commit()
    return maquina


def listar_maquinas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Maquina]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Maquina).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Maquina.alias).all())
