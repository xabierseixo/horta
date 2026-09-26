from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_cultivo. Queda fóra id,
# parcela_id e created_at: mover un cultivo a outra parcela saltaría o
# control de permisos, que se fai coa parcela_id actual.
CAMPOS_EDITABLES_CULTIVO = frozenset(
    {
        "especie",
        "variedade",
        "data_sementeira",
        "data_plantacion",
        "data_colleita_prevista",
        "data_colleita_real",
        "cantidade",
        "unidade",
        "notas",
        "estado",
    }
)


def _horta_id_da_parcela(session: Session, parcela_id: int) -> int | None:
    return session.query(Parcela.horta_id).filter_by(id=parcela_id).scalar()


def crear_cultivo(
    session: Session,
    actor: Usuario,
    parcela_id: int,
    especie: str,
    **campos: Any,
) -> Cultivo:
    horta_id = _horta_id_da_parcela(session, parcela_id)
    if horta_id is None:
        raise ValueError("Esa parcela non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    estado = campos.pop("estado", "planificado")
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, estado=estado, **campos)
    session.add(cultivo)
    session.commit()
    return cultivo


def actualizar_cultivo(
    session: Session,
    actor: Usuario,
    cultivo: Cultivo,
    **cambios: Any,
) -> Cultivo:
    non_editables = set(cambios) - CAMPOS_EDITABLES_CULTIVO
    if non_editables:
        raise ValueError(f"Campos non editables nun cultivo: {', '.join(sorted(non_editables))}")
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(cultivo, campo, valor)
    session.commit()
    return cultivo


def eliminar_cultivo(session: Session, actor: Usuario, cultivo: Cultivo) -> None:
    """Elimina o cultivo e, en cascada, os seus tratamentos e fertilizacións.

    A diferenza de eliminar_tratamento/eliminar_fertilizacion (baixa lóxica),
    aquí bórranse fisicamente: non ten sentido conservar por baixa lóxica un
    tratamento cuxo cultivo xa non existe.
    """
    horta_id = _horta_id_da_parcela(session, cultivo.parcela_id)
    if horta_id is None:
        raise ValueError("A parcela deste cultivo xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    session.query(Tarefa).filter_by(cultivo_id=cultivo.id).update({"cultivo_id": None})
    for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
        session.delete(tratamento)
    for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
        session.delete(fertilizacion)
    session.flush()
    session.delete(cultivo)
    session.commit()


def listar_cultivos(session: Session, actor: Usuario, horta_id: int) -> list[Cultivo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Cultivo)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
        .order_by(Cultivo.especie)
        .all()
    )
