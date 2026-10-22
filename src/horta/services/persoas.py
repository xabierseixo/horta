from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Patrón oficial do descritor SIEX (Anexo VI, folla "Patrones texto") para NIF de persoa física.
_PATRON_NIF = re.compile(r"^[KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$")

CAMPOS_EDITABLES_PERSOA = frozenset(
    {"nome", "apelidos", "nif", "e_aplicador", "e_asesor", "ropo_numero", "ropo_tipo_carne",
     "ropo_caducidade", "regfer_numero", "activa"}
)


def _normalizar_e_validar(datos: dict[str, Any]) -> None:
    if datos.get("nif"):
        datos["nif"] = datos["nif"].strip().upper()
        if not _PATRON_NIF.match(datos["nif"]):
            raise OperacionNonPermitidaError("O NIF non é válido")
    if datos.get("e_aplicador") and not (datos.get("ropo_numero") and datos.get("ropo_caducidade")):
        raise OperacionNonPermitidaError(
            "Un aplicador precisa o nº ROPO e a data de caducidade do carné"
        )
    if datos.get("e_asesor") and not datos.get("ropo_numero"):
        raise OperacionNonPermitidaError("Un asesor precisa o nº ROPO")


def crear_persoa(
    session: Session, actor: Usuario, horta_id: int, nome: str, **campos: Any
) -> Persoa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _normalizar_e_validar(campos)
    persoa = Persoa(horta_id=horta_id, nome=nome, **campos)
    session.add(persoa)
    session.commit()
    return persoa


def actualizar_persoa(session: Session, actor: Usuario, persoa: Persoa, **cambios: Any) -> Persoa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PERSOA
    if non_editables:
        raise ValueError(f"Campos non editables nunha persoa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_ESCRITURA)
    resultado = {c: getattr(persoa, c) for c in CAMPOS_EDITABLES_PERSOA} | cambios
    _normalizar_e_validar(resultado)
    for campo in cambios:
        setattr(persoa, campo, resultado[campo])
    session.commit()
    return persoa


def listar_persoas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Persoa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Persoa.nome).all())


def ropo_vixente(persoa: Persoa, na_data: date) -> bool:
    return persoa.ropo_caducidade is not None and persoa.ropo_caducidade >= na_data
