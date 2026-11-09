"""Servizo de rexistro e consulta de accesos de inspección e auditoría (tarefa 182b)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session, joinedload

from horta.models.acceso import RexistroAcceso
from horta.models.horta import HortaMembro, RolHorta
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta


def rexistrar_acceso(
    session: Session,
    usuario: Usuario,
    horta_id: int,
    seccion: str,
    agora: datetime | None = None,
) -> RexistroAcceso | None:
    """Rexistra o acceso dun membro de inspección ou auditoría a unha sección da explotación.

    Só garda o rexistro se o membro ten data de fin de acceso (acceso_ata), evitando encher
    a táboa co traballo diario do equipo habitual.
    """
    usuario_id = usuario.id
    membro = session.get(HortaMembro, (horta_id, usuario_id))
    if membro is None or membro.acceso_ata is None:
        return None

    data_hora = agora or datetime.now(timezone.utc).replace(tzinfo=None)
    rexistro = RexistroAcceso(
        horta_id=horta_id,
        usuario_id=usuario_id,
        data_hora=data_hora,
        seccion=seccion,
    )
    session.add(rexistro)
    session.commit()
    return rexistro


def listar_accesos(
    session: Session,
    actor: Usuario,
    horta_id: int,
) -> list[RexistroAcceso]:
    """Lista os accesos de inspección e auditoría da explotación (só para ADMIN).

    Devolve os rexistros ordenados do máis recente ao máis antigo, coa conta asociada cargada.
    """
    comprobar_rol_horta(session, horta_id, actor, {RolHorta.ADMIN})
    return list(
        session.query(RexistroAcceso)
        .options(joinedload(RexistroAcceso.usuario))
        .filter(RexistroAcceso.horta_id == horta_id)
        .order_by(RexistroAcceso.data_hora.desc(), RexistroAcceso.id.desc())
        .all()
    )


__all__ = [
    "listar_accesos",
    "rexistrar_acceso",
]
