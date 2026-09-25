from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Queda fóra cultivo_id, id, created_at e baixa: baixa só se cambia dende
# eliminar_tratamento (baixa lóxica), nunca dende unha actualización xenérica.
CAMPOS_EDITABLES_TRATAMENTO = frozenset(
    {
        "data",
        "praga",
        "superficie_tratada",
        "produto",
        "numero_rexistro_produto",
        "dose",
        "eficacia",
        "aplicador",
        "equipo_aplicador",
        "persoas_asesoramento",
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


def crear_tratamento(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    data: Any,
    praga: str,
    produto: str,
    aplicador: str,
    **campos: Any,
) -> Tratamento:
    horta_id = _horta_id_do_cultivo(session, cultivo_id)
    if horta_id is None:
        raise ValueError("Ese cultivo non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    tratamento = Tratamento(
        cultivo_id=cultivo_id,
        data=data,
        praga=praga,
        produto=produto,
        aplicador=aplicador,
        **campos,
    )
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento(
    session: Session,
    actor: Usuario,
    tratamento: Tratamento,
    **cambios: Any,
) -> Tratamento:
    non_editables = set(cambios) - CAMPOS_EDITABLES_TRATAMENTO
    if non_editables:
        raise ValueError(f"Campos non editables nun tratamento: {', '.join(sorted(non_editables))}")
    horta_id = _horta_id_do_cultivo(session, tratamento.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo deste tratamento xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    for campo, valor in cambios.items():
        setattr(tratamento, campo, valor)
    session.commit()
    return tratamento


def eliminar_tratamento(session: Session, actor: Usuario, tratamento: Tratamento) -> None:
    """Dá de baixa o tratamento (baixa lóxica).

    Nunca se borra fisicamente: a normativa esixe conservar estes rexistros
    un mínimo de 3 anos (README §22). Deixa de aparecer en listar_tratamentos,
    pero a fila segue na base de datos.
    """
    horta_id = _horta_id_do_cultivo(session, tratamento.cultivo_id)
    if horta_id is None:
        raise ValueError("O cultivo deste tratamento xa non existe")
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos(session: Session, actor: Usuario, horta_id: int) -> list[Tratamento]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(Tratamento)
        .join(Cultivo, Tratamento.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id, Tratamento.baixa.is_(False))
        .order_by(Tratamento.data.desc())
        .all()
    )
