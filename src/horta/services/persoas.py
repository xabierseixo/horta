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
     "ropo_caducidade", "regfer_numero", "activa", "e_titular", "e_traballador", "telefono",
     "email", "vinculo", "horas_ano", "formacion_agraria", "xenero", "data_nacemento",
     "discapacidade", "enderezo", "localidade", "codigo_postal", "provincia"}
)


VINCULOS = ("titular", "familiar", "asalariado", "socio", "externo")
XENEROS = ("muller", "home", "outro")


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
    if datos.get("vinculo") not in (None, *VINCULOS):
        raise OperacionNonPermitidaError(f"Vínculo non válido: {datos['vinculo']}")
    if datos.get("horas_ano") is not None and not 0 <= datos["horas_ano"] <= 4000:
        raise OperacionNonPermitidaError("As horas ao ano teñen que estar entre 0 e 4.000")
    if datos.get("xenero") not in (None, *XENEROS):
        raise OperacionNonPermitidaError(f"Xénero non válido: {datos['xenero']}")
    if datos.get("data_nacemento") is not None and datos["data_nacemento"] > date.today():
        raise OperacionNonPermitidaError("A data de nacemento non pode ser futura")


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


def comprobar_quen(
    session: Session, horta_id: int, persoa_id: int | None, horas: float | None,
    obrigatoria: bool = True,
) -> None:
    """Todo traballo o fai unha persoa: tense que indicar e ten que ser desta explotación.
    As horas son opcionais."""
    if persoa_id is None:
        if obrigatoria:
            raise OperacionNonPermitidaError("Indica quen o fixo")
    else:
        persoa = session.get(Persoa, persoa_id)
        if persoa is None or persoa.horta_id != horta_id:
            raise OperacionNonPermitidaError("A persoa indicada non é desta explotación")
    if horas is not None and horas <= 0:
        raise OperacionNonPermitidaError("As horas teñen que ser máis de 0")
