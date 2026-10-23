"""Que lle falta a unha explotación profesional para estar en regra."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.animal import Animal
from horta.models.horta import Horta, RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import ropo_vixente

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
    if not horta.uso_profesional:
        return []
    hoxe = hoxe or date.today()
    aplicadores = [
        p
        for p in session.query(Persoa).filter_by(horta_id=horta.id, activa=True, e_aplicador=True)
        if ropo_vixente(p, hoxe)
    ]
    ten_animais = session.query(Animal).filter_by(horta_id=horta.id).first() is not None
    requisitos = [
        Requisito(
            "NIF do titular",
            bool(horta.titular_nif),
            "Indícao en «Configurar explotación».",
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
        requisitos.append(
            Requisito(
                "Código REGA do gando",
                bool(horta.codigo_rega),
                "Solicítase na Oficina Agraria Comarcal.",
            )
        )
    return requisitos
