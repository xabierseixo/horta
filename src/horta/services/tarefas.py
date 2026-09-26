from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra id, horta_id e created_at: horta_id non se edita (control de
# permisos baseado nel), created_at non ten sentido editar. estado e
# data_feita tampouco: só cambian dende marcar_feita/marcar_pendente.
CAMPOS_EDITABLES_TAREFA = frozenset(
    {
        "parcela_id",
        "cultivo_id",
        "descricion",
        "data",
        "data_limite",
        "prioridade",
        "notas",
    }
)


def crear_tarefa(
    session: Session,
    actor: Usuario,
    horta_id: int,
    descricion: str,
    **campos: Any,
) -> Tarefa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    prioridade = campos.pop("prioridade", "media")
    tarefa = Tarefa(horta_id=horta_id, descricion=descricion, prioridade=prioridade, **campos)
    session.add(tarefa)
    session.commit()
    return tarefa


def actualizar_tarefa(
    session: Session,
    actor: Usuario,
    tarefa: Tarefa,
    **cambios: Any,
) -> Tarefa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_TAREFA
    if non_editables:
        raise ValueError(f"Campos non editables nunha tarefa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(tarefa, campo, valor)
    session.commit()
    return tarefa


def marcar_feita(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    tarefa.estado = "feito"
    tarefa.data_feita = date.today()
    session.commit()
    return tarefa


def marcar_pendente(session: Session, actor: Usuario, tarefa: Tarefa) -> Tarefa:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    tarefa.estado = "pendente"
    tarefa.data_feita = None
    session.commit()
    return tarefa


def eliminar_tarefa(session: Session, actor: Usuario, tarefa: Tarefa) -> None:
    comprobar_rol_horta(session, tarefa.horta_id, actor, _ROLES_ESCRITURA)
    session.delete(tarefa)
    session.commit()


def listar_tarefas(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Tarefa).filter_by(horta_id=horta_id).order_by(Tarefa.data).all())


def listar_tarefas_pendentes_hoxe(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter_by(horta_id=horta_id, estado="pendente", data=date.today())
        .order_by(Tarefa.prioridade)
        .all()
    )


def listar_tarefas_proximas(
    session: Session, actor: Usuario, horta_id: int, limite: int = 5
) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter(
            Tarefa.horta_id == horta_id,
            Tarefa.estado == "pendente",
            Tarefa.data > date.today(),
        )
        .order_by(Tarefa.data)
        .limit(limite)
        .all()
    )


def listar_tarefas_atrasadas(session: Session, actor: Usuario, horta_id: int) -> list[Tarefa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tarefa)
        .filter(
            Tarefa.horta_id == horta_id,
            Tarefa.estado == "pendente",
            Tarefa.data_limite.is_not(None),
            Tarefa.data_limite < date.today(),
        )
        .order_by(Tarefa.data_limite)
        .all()
    )


def contar_tarefas_pendentes(session: Session, actor: Usuario, horta_id: int) -> int:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return session.query(Tarefa).filter_by(horta_id=horta_id, estado="pendente").count()
