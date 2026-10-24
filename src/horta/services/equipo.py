"""Equipo da explotación: persoas, as súas funcións e o seu acceso á app.

O acceso gárdase en HortaMembro (fronteira de seguridade); a persoa liga coa súa conta
por usuario_id. Deseño: o deseño
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from horta.models.horta import HortaMembro, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.auth import normalizar_email
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import (
    cambiar_rol_membro,
    comprobar_rol_horta,
    engadir_membro,
    quitar_membro,
)

HORAS_UTA = 1920
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def acceso_da_persoa(session: Session, persoa: Persoa) -> RolHorta | None:
    if persoa.usuario_id is None:
        return None
    membro = session.get(HortaMembro, (persoa.horta_id, persoa.usuario_id))
    return membro.rol if membro else None


def conceder_acceso(
    session: Session, actor: Usuario, persoa: Persoa, email: str, rol: RolHorta
) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    usuario = session.query(Usuario).filter_by(email=normalizar_email(email)).one_or_none()
    if usuario is None:
        raise OperacionNonPermitidaError(
            "Non hai ningunha conta con ese email. Pídelle ao administrador que a cree."
        )
    outra = (
        session.query(Persoa)
        .filter(Persoa.horta_id == persoa.horta_id, Persoa.usuario_id == usuario.id,
                Persoa.id != persoa.id)
        .first()
    )
    if outra is not None:
        raise OperacionNonPermitidaError(f"Esa conta xa está ligada a {outra.nome}")
    if session.get(HortaMembro, (persoa.horta_id, usuario.id)) is None:
        engadir_membro(session, actor, persoa.horta_id, usuario, rol)
    else:
        cambiar_rol_membro(session, actor, persoa.horta_id, usuario.id, rol)
    persoa.usuario_id = usuario.id
    session.commit()


def retirar_acceso(session: Session, actor: Usuario, persoa: Persoa) -> None:
    comprobar_rol_horta(session, persoa.horta_id, actor, {RolHorta.ADMIN})
    if persoa.usuario_id is None:
        return
    quitar_membro(session, actor, persoa.horta_id, persoa.usuario_id)
    persoa.usuario_id = None
    session.commit()


def uta_equipo(session: Session, actor: Usuario, horta_id: int) -> float:
    """Unidades de traballo agrario: horas ao ano das persoas activas / 1.920."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    horas = sum(
        p.horas_ano or 0
        for p in session.query(Persoa).filter_by(horta_id=horta_id, activa=True)
    )
    return round(horas / HORAS_UTA, 2)
