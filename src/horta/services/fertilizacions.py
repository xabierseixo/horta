from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Fertilizacion
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra cultivo_id, id, created_at e baixa: baixa só se cambia dende
# eliminar_fertilizacion (baixa lóxica), nunca dende unha actualización xenérica.
CAMPOS_EDITABLES_FERTILIZACION = frozenset(
    {
        "data",
        "superficie",
        "tipo",
        "produto",
        "dose",
        "n",
        "p",
        "k",
        "carbono_organico",
        "micronutrientes",
        "asesoramento_recibido",
        "notas",
    }
)


def _horta_id_do_cultivo(session: Session, cultivo_id: int) -> int | None:
    return (
        session.query(Parcela.horta_id)
        .join(Cultivo, Cultivo.parcela_id == Parcela.id)
        .filter(Cultivo.id == cultivo_id)
        .scalar()
    )


def crear_fertilizacion(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    data: Any,
    tipo: str,
    produto: str,
    **campos: Any,
) -> Fertilizacion:
    horta_id = _horta_id_do_cultivo(session, cultivo_id)
    if horta_id is None:
        raise ValueError("Ese cultivo non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    fertilizacion = Fertilizacion(
        cultivo_id=cultivo_id,
        data=data,
        tipo=tipo,
        produto=produto,
        **campos,
    )
    session.add(fertilizacion)
    session.commit()
    return fertilizacion


def actualizar_fertilizacion(
    session: Session,
    actor: Usuario,
    fertilizacion: Fertilizacion,
    **cambios: Any,
) -> Fertilizacion:
    non_editables = set(cambios) - CAMPOS_EDITABLES_FERTILIZACION
    if non_editables:
        raise ValueError(
            f"Campos non editables nunha fertilización: {', '.join(sorted(non_editables))}"
        )
    horta_id = _horta_id_do_cultivo(session, fertilizacion.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo desta fertilización xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(fertilizacion, campo, valor)
    session.commit()
    return fertilizacion


def eliminar_fertilizacion(session: Session, actor: Usuario, fertilizacion: Fertilizacion) -> None:
    """Dá de baixa a fertilización (baixa lóxica).

    Nunca se borra fisicamente: a normativa esixe conservar estes rexistros
    un mínimo de 3 anos (README §22). Deixa de aparecer en
    listar_fertilizacions, pero a fila segue na base de datos.
    """
    horta_id = _horta_id_do_cultivo(session, fertilizacion.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo desta fertilización xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    fertilizacion.baixa = True
    session.commit()


def listar_fertilizacions(session: Session, actor: Usuario, horta_id: int) -> list[Fertilizacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Fertilizacion)
        .join(Cultivo, Fertilizacion.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id, Fertilizacion.baixa.is_(False))
        .order_by(Fertilizacion.data.desc())
        .all()
    )
