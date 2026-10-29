from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import RolHorta
from horta.models.movemento_animal import MovementoAnimal
from horta.models.outro_traballo import OutroTraballo
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.coidados_animais import ten_coidados
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.movementos_animais import (
    INICIAL,
    cambiar_data_alta,
    crear_inicial,
    recalcular,
    ten_movementos,
)
from horta.services.pastoreos import ten_pastoreo
from horta.services.producions_animais import ten_producion

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_animal. Quedan fóra id,
# horta_id e created_at: mover un animal a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual. A cantidade, a baixa e o
# estado saen das entradas e saídas (services.movementos_animais).
CAMPOS_EDITABLES_ANIMAL = frozenset(
    {"especie", "especie_codigo", "raza", "data_alta", "notas"}
)

# As especies de granxa do catálogo oficial ESPECIE_ANIMAL, en galego
ESPECIES: dict[str, str] = {
    "06": "Galiñas", "16": "Coellos", "18": "Abellas", "03": "Ovellas", "04": "Cabras",
    "02": "Porcos", "01": "Vacas", "05": "Cabalos e burros", "07": "Pavos",
    "08": "Pintadas", "09": "Patos", "10": "Gansos", "11": "Paspallás", "12": "Pombas",
    "13": "Faisáns", "14": "Perdices", "15": "Avestruces e outras ratites", "17": "Lebres",
    "23": "Cervos", "24": "Corzos", "25": "Gamos", "26": "Xabarís", "27": "Caracois",
    "28": "Ras",
}


def _validar_cantidade(campos: dict[str, Any]) -> None:
    if "cantidade" in campos and campos["cantidade"] is not None:
        if campos["cantidade"] < 1:
            raise OperacionNonPermitidaError("A cantidade ten que ser polo menos 1")


def _validar_especie(session: Session, codigo: str | None, na_data: date) -> None:
    if codigo is not None:
        if codigo not in ESPECIES:
            raise OperacionNonPermitidaError("Escolle a especie da lista")
        validar_codigo(session, "especie_animal", codigo, na_data)


def crear_animal(
    session: Session,
    actor: Usuario,
    horta_id: int,
    especie: str,
    data_alta: date,
    **campos: Any,
) -> Animal:
    """Un grupo de animais. A cantidade inicial queda como o seu primeiro movemento."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_cantidade(campos)
    _validar_especie(session, campos.get("especie_codigo"), data_alta)
    cantidade = campos.pop("cantidade", 1)
    for derivado in ("estado", "data_baixa"):
        campos.pop(derivado, None)
    animal = Animal(horta_id=horta_id, especie=especie, data_alta=data_alta,
                    cantidade=cantidade, estado="activo", **campos)
    session.add(animal)
    session.flush()
    crear_inicial(session, animal, cantidade)
    recalcular(session, animal)
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
    data_alta = cambios.pop("data_alta", animal.data_alta)
    _validar_especie(session, cambios.get("especie_codigo"), data_alta)
    if data_alta != animal.data_alta:
        primeiro = (session.query(MovementoAnimal)
                    .filter(MovementoAnimal.animal_id == animal.id,
                            MovementoAnimal.tipo != INICIAL, MovementoAnimal.baixa.is_(False))
                    .order_by(MovementoAnimal.data).first())
        if primeiro is not None and primeiro.data < data_alta:
            raise OperacionNonPermitidaError(
                f"Hai entradas ou saídas desde o {primeiro.data:%d/%m/%Y}: "
                "a data de alta non pode ser posterior")
        cambiar_data_alta(session, animal, data_alta)
    for campo, valor in cambios.items():
        setattr(animal, campo, valor)
    recalcular(session, animal)
    session.commit()
    return animal


def eliminar_animal(session: Session, actor: Usuario, animal: Animal) -> None:
    comprobar_rol_horta(session, animal.horta_id, actor, _ROLES_ESCRITURA)
    if (ten_coidados(session, animal.id) or ten_movementos(session, animal.id)
            or ten_producion(session, animal.id) or ten_pastoreo(session, animal.id)):
        raise OperacionNonPermitidaError(
            "Este grupo ten coidados, entradas e saídas, produción ou pastoreos apuntados e debe "
            "conservarse (obriga legal). Se xa non ten animais, apunta a súa saída ou morte")
    session.query(Tarefa).filter_by(animal_id=animal.id).update({"animal_id": None})
    session.query(OutroTraballo).filter_by(animal_id=animal.id).update({"animal_id": None})
    session.query(MovementoAnimal).filter_by(animal_id=animal.id).delete()
    session.delete(animal)
    session.commit()


def listar_animais(session: Session, actor: Usuario, horta_id: int) -> list[Animal]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Animal).filter_by(horta_id=horta_id).order_by(Animal.especie).all())
