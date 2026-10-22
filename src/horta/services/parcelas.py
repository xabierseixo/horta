from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.tarefa import Tarefa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Campos que se poden modificar dende actualizar_parcela. Quedan fóra id,
# horta_id e created_at: mover unha parcela a outra horta saltaría o control
# de permisos, que se fai coa horta_id actual.
CAMPOS_EDITABLES_PARCELA = frozenset(
    {
        "nome",
        "descricion",
        "superficie",
        "posicion",
        "uso_aproveitamento",
        "secano_regadio",
        "sigpac_provincia",
        "sigpac_concello",
        "sigpac_poligono",
        "sigpac_parcela",
        "sigpac_subparcela",
        "notas",
        "estado",
        "lat",
        "lon",
        "geometria",
        "imaxe",
    }
)


def _validar_coordenadas(campos: dict[str, Any]) -> None:
    if "lat" in campos and campos["lat"] is not None:
        if not (-90 <= campos["lat"] <= 90):
            raise OperacionNonPermitidaError("A latitude debe estar entre -90 e 90")
    if "lon" in campos and campos["lon"] is not None:
        if not (-180 <= campos["lon"] <= 180):
            raise OperacionNonPermitidaError("A lonxitude debe estar entre -180 e 180")


def _validar_superficie(campos: dict[str, Any]) -> None:
    if "superficie" in campos and campos["superficie"] is not None:
        if campos["superficie"] < 0:
            raise OperacionNonPermitidaError("A superficie non pode ser negativa")


def crear_parcela(
    session: Session,
    actor: Usuario,
    horta_id: int,
    nome: str,
    **campos: Any,
) -> Parcela:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_coordenadas(campos)
    _validar_superficie(campos)
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
    non_editables = set(cambios) - CAMPOS_EDITABLES_PARCELA
    if non_editables:
        raise ValueError(f"Campos non editables nunha parcela: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    _validar_coordenadas(cambios)
    _validar_superficie(cambios)
    for campo, valor in cambios.items():
        setattr(parcela, campo, valor)
    session.commit()
    return parcela


def eliminar_parcela(session: Session, actor: Usuario, parcela: Parcela) -> None:
    comprobar_rol_horta(session, parcela.horta_id, actor, _ROLES_ESCRITURA)
    session.query(Tarefa).filter_by(parcela_id=parcela.id).update({"parcela_id": None})
    cultivos = session.query(Cultivo).filter_by(parcela_id=parcela.id).all()
    for cultivo in cultivos:
        for tratamento in session.query(Tratamento).filter_by(cultivo_id=cultivo.id).all():
            session.delete(tratamento)
        for fertilizacion in session.query(Fertilizacion).filter_by(cultivo_id=cultivo.id).all():
            session.delete(fertilizacion)
    # Igual que en eliminar_horta: sen relationship(), forzar estes borrados
    # á BD antes de borrar os seus Cultivo pai.
    session.flush()
    for cultivo in cultivos:
        session.delete(cultivo)
    session.flush()
    session.delete(parcela)
    session.commit()


def listar_parcelas(session: Session, actor: Usuario, horta_id: int) -> list[Parcela]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Parcela).filter_by(horta_id=horta_id).order_by(Parcela.nome).all())
