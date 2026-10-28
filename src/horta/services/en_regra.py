"""Que lle falta a unha explotación para estar en regra (REGA tamén se non é profesional)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import Horta, RolHorta
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import con_papel, ropo_vixente, titular_da_horta

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass(frozen=True)
class Requisito:
    texto: str
    cumprido: bool
    axuda: str


def requisitos_en_regra(
    session: Session, actor: Usuario, horta: Horta, hoxe: date | None = None
) -> list[Requisito]:
    comprobar_rol_horta(session, horta.id, actor, _ROLES_LECTURA)
    ten_animais = (
        session.query(Animal).filter_by(horta_id=horta.id, data_baixa=None).first() is not None
    )
    requisito_rega = Requisito(
        "Código REGA do gando",
        bool(horta.codigo_rega),
        "Solicítase na Oficina Agraria Comarcal, tamén para galiñas de autoconsumo.",
    )
    if not horta.uso_profesional:
        return [requisito_rega] if ten_animais else []
    hoxe = hoxe or date.today()
    aplicadores = [p for p in con_papel(session, horta.id, "aplicador") if ropo_vixente(p, hoxe)]
    titular = titular_da_horta(session, horta.id)
    requisitos = [
        Requisito(
            "NIF do titular",
            bool(titular and titular.nif),
            "Indica en «Persoas» quen é o titular e o seu NIF.",
        ),
        Requisito(
            "Inscrición no REAGA",
            bool(horta.codigo_reaga),
            "Solicítase na Oficina Agraria Comarcal ou na sede electrónica da Xunta.",
        ),
        Requisito(
            "Aplicador con carné ROPO en vigor",
            bool(aplicadores),
            "Dáo de alta na sección «Persoas».",
        ),
    ]
    if ten_animais:
        requisitos.append(requisito_rega)
    return requisitos
