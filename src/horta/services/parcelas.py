from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def crear_parcela(
    session: Session,
    actor: Usuario,
    horta_id: int,
    nome: str,
    **campos: Any,
) -> Parcela:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "activa")
    parcela = Parcela(horta_id=horta_id, nome=nome, estado=estado, **campos)
    session.add(parcela)
    session.commit()
    return parcela


def actualizar_parcela(
    session: Session,
    actor: Usuario,
    parcela: Parcela,
    **cambios: Any,
) -> Parcela:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
    session.commit()
    return parcela


def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(parcela)
    session.commit()


def listar_parcelas(session: Session, actor: Usuario, horta_id: int) -> list[Parcela]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(Parcela.nome).all())
