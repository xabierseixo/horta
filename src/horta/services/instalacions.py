"""Instalacións da explotación (paso 14): almacéns, galiñeiros, cortes, invernadoiros…"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.idiomas import N_
from horta.models.horta import RolHorta
from horta.models.instalacion import Instalacion
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_INSTALACION: dict[str, str] = {
    "almacen": N_("Almacén"),
    "galineiro": N_("Galiñeiro"),
    "corte": N_("Corte, cortello ou cuadra"),
    "colmear": N_("Colmear"),
    "invernadoiro": N_("Invernadoiro"),
    "nave": N_("Nave ou alpendre"),
    "transformacion": N_("Obradoiro de transformación"),
    "outra": N_("Outra"),
}
CAMPOS_EDITABLES_INSTALACION = frozenset(
    {"tipo", "nome", "enderezo", "referencia_catastral", "notas", "activa"})


def _validar(campos: dict[str, Any]) -> None:
    if "tipo" in campos and campos["tipo"] not in TIPOS_INSTALACION:
        raise OperacionNonPermitidaError("Escolle que tipo de instalación é")
    if "nome" in campos and not (campos["nome"] or "").strip():
        raise OperacionNonPermitidaError("O nome non pode quedar baleiro")


def crear_instalacion(session: Session, actor: Usuario, horta_id: int, tipo: str, nome: str,
                      **campos: Any) -> Instalacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar({"tipo": tipo, "nome": nome})
    if set(campos) - CAMPOS_EDITABLES_INSTALACION:
        raise ValueError("Campos non editables nunha instalación")
    instalacion = Instalacion(horta_id=horta_id, tipo=tipo, nome=nome.strip(), **campos)
    session.add(instalacion)
    session.commit()
    return instalacion


def actualizar_instalacion(session: Session, actor: Usuario, instalacion: Instalacion,
                           **cambios: Any) -> Instalacion:
    comprobar_rol_horta(session, instalacion.horta_id, actor, _ROLES_ESCRITURA)
    if set(cambios) - CAMPOS_EDITABLES_INSTALACION:
        raise ValueError("Campos non editables nunha instalación")
    _validar(cambios)
    for campo, valor in cambios.items():
        setattr(instalacion, campo, valor)
    session.commit()
    return instalacion


def listar_instalacions(session: Session, actor: Usuario, horta_id: int,
                        so_activas: bool = False) -> list[Instalacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Instalacion).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return sorted(consulta, key=lambda i: i.nome.lower())


def comprobar_instalacion(session: Session, horta_id: int, instalacion_id: int | None) -> None:
    """A instalación dun animal ou traballo (opcional) ten que ser desta explotación."""
    if instalacion_id is None:
        return
    instalacion = session.get(Instalacion, instalacion_id)
    if instalacion is None or instalacion.horta_id != horta_id:
        raise OperacionNonPermitidaError("A instalación non é desta explotación")
