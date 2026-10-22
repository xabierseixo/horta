from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_animal. Quedan fóra id,
# horta_id e created_at: mover un animal a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual.
CAMPOS_EDITABLES_ANIMAL = frozenset(
    {"especie", "raza", "cantidade", "data_alta", "data_baixa", "estado", "notas"}
)


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 1:
            raise OperacionNonPermitidaError("A cantidade ten que ser polo menos 1")


def crear_animal(
    session: Session,
    actor: Usuario,
    horta_id: int,
    especie: str,
    data_alta: date,
    **campos: Any,
) -> Animal:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    estado = campos.pop("estado", "activo")
    animal = Animal(
        horta_id=horta_id, especie=especie, data_alta=data_alta, estado=estado, **campos
    )
    session.add(animal)
    session.commit()
    return animal


def actualizar_animal(
    session: Session,
    actor: Usuario,
    animal: Animal,
    **cambios: Any,
) -> Animal:
    non_editables = set(cambios) - CAMPOS_EDITABLES_ANIMAL
    if non_editables:
        raise ValueError(f"Campos non editables nun animal: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(cambios)
    for campo, valor in cambios.items():
        setattr(animal, campo, valor)
    session.commit()
    return animal


def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(animal)
    session.commit()


def listar_animais(session: Session, actor: Usuario, horta_id: int) -> list[Animal]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Animal).filter_by(horta_id=horta_id).order_by(Animal.especie).all())
