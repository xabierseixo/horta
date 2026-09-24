from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import Horta, HortaMembro, RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError

# Campos que se poden modificar dende actualizar_horta. Queda fóra id e
# created_at, que non teñen sentido editar.
CAMPOS_EDITABLES_HORTA = frozenset({"nome", "descricion", "uso_profesional"})


def _obter_membro(session: Session, horta_id: int, usuario_id: int) -> HortaMembro | None:
    return session.get(HortaMembro, (horta_id, usuario_id))


def _e_ultimo_admin_da_horta(session: Session, membro: HortaMembro) -> bool:
    if membro.rol != RolHorta.ADMIN:
        return False
    admins = (
        session.query(HortaMembro).filter_by(horta_id=membro.horta_id, rol=RolHorta.ADMIN).count()
    )
    return admins <= 1


def comprobar_rol_horta(
    session: Session,
    horta_id: int,
    usuario: Usuario,
    roles_permitidos: set[RolHorta],
) -> HortaMembro:
    membro = _obter_membro(session, horta_id, usuario.id)
    if membro is None or membro.rol not in roles_permitidos:
        raise PermisoDenegadoError("Non tes permiso suficiente nesta horta")
    return membro


def crear_horta(
    session: Session,
    actor: Usuario,
    nome: str,
    descricion: str | None = None,
    uso_profesional: bool = False,
) -> Horta:
    horta = Horta(nome=nome, descricion=descricion, uso_profesional=uso_profesional)
    session.add(horta)
    session.flush()
    membro = HortaMembro(horta_id=horta.id, usuario_id=actor.id, rol=RolHorta.ADMIN)
    session.add(membro)
    session.commit()
    return horta


def actualizar_horta(
    session: Session,
    actor: Usuario,
    horta: Horta,
    **cambios: Any,
) -> Horta:
    non_editables = set(cambios) - CAMPOS_EDITABLES_HORTA
    if non_editables:
        raise ValueError(f"Campos non editables nunha horta: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    for campo, valor in cambios.items():
        setattr(horta, campo, valor)
    session.commit()
    return horta


def eliminar_horta(session: Session, actor: Usuario, horta: Horta) -> None:
    """Elimina a horta e todo o que dependa dela (parcelas, animais, membros).

    Non hai borrado en cascada a nivel de base de datos (sen relacións
    SQLAlchemy nin FKs ON DELETE CASCADE), así que hai que borrar
    explicitamente os rexistros dependentes antes da propia horta.
    """
    comprobar_rol_horta(session, horta.id, actor, {RolHorta.ADMIN})
    for parcela in session.query(Parcela).filter_by(horta_id=horta.id).all():
        session.delete(parcela)
    for animal in session.query(Animal).filter_by(horta_id=horta.id).all():
        session.delete(animal)
    for membro in session.query(HortaMembro).filter_by(horta_id=horta.id).all():
        session.delete(membro)
    session.delete(horta)
    session.commit()


def engadir_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo: Usuario,
    rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = HortaMembro(horta_id=horta_id, usuario_id=usuario_obxectivo.id, rol=rol)
    session.add(membro)
    session.commit()
    return membro


def cambiar_rol_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
    novo_rol: RolHorta,
) -> HortaMembro:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is None:
        raise OperacionNonPermitidaError("Ese usuario non é membro desta horta")
    if novo_rol != RolHorta.ADMIN and _e_ultimo_admin_da_horta(session, membro):
        raise OperacionNonPermitidaError("A horta ten que ter polo menos un administrador")
    membro.rol = novo_rol
    session.commit()
    return membro


def quitar_membro(
    session: Session,
    actor: Usuario,
    horta_id: int,
    usuario_obxectivo_id: int,
) -> None:
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    membro = _obter_membro(session, horta_id, usuario_obxectivo_id)
    if membro is not None:
        if _e_ultimo_admin_da_horta(session, membro):
            raise OperacionNonPermitidaError("A horta ten que ter polo menos un administrador")
        session.delete(membro)
        session.commit()


def listar_hortas_usuario(session: Session, usuario: Usuario) -> list[tuple[Horta, RolHorta]]:
    membros = session.query(HortaMembro).filter_by(usuario_id=usuario.id).all()
    resultado: list[tuple[Horta, RolHorta]] = []
    for membro in membros:
        horta = session.get(Horta, membro.horta_id)
        assert horta is not None
        resultado.append((horta, membro.rol))
    return resultado
