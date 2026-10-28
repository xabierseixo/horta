"""As leiras dun traballo (labor, rega, abonado): unha ou varias, como no tratamento e no
pastoreo."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela
from horta.services.errors import OperacionNonPermitidaError


@dataclass
class LeiraTraballo:
    cultivo_id: int
    # Baleiro: a do cultivo
    superficie_ha: float | None = None


@dataclass
class LeiraValida:
    cultivo: Cultivo
    parcela: Parcela
    superficie_ha: float | None


def as_leiras(cultivo_id: int | None, superficie_ha: float | None,
              leiras: list[LeiraTraballo]) -> list[LeiraTraballo]:
    """As leiras do traballo: a lista, ou unha soa (cultivo_id e superficie_ha) para apuntar
    nun só cultivo."""
    if leiras:
        return leiras
    return [LeiraTraballo(cultivo_id, superficie_ha)] if cultivo_id is not None else []


def validar_leiras(session: Session, leiras: list[LeiraTraballo],
                   horta_id: int | None = None) -> tuple[int, list[LeiraValida]]:
    """Polo menos unha, sen repetir, todas da mesma explotación (a do traballo, se xa a ten)
    e coa superficie dentro da do seu cultivo. Devolve a explotación e as leiras."""
    if not leiras:
        raise OperacionNonPermitidaError("Escolle polo menos unha leira")
    if len({leira.cultivo_id for leira in leiras}) != len(leiras):
        raise OperacionNonPermitidaError("Hai unha leira repetida")
    validas = []
    for leira in leiras:
        cultivo = session.get(Cultivo, leira.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None:
            raise OperacionNonPermitidaError("Ese cultivo non existe")
        if horta_id is None:
            horta_id = parcela.horta_id
        elif parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
        if leira.superficie_ha is not None:
            if leira.superficie_ha <= 0:
                raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
            if cultivo.superficie_ha and leira.superficie_ha > cultivo.superficie_ha:
                raise OperacionNonPermitidaError(
                    f"A superficie en {parcela.nome} é maior ca do cultivo")
        validas.append(LeiraValida(cultivo, parcela,
                                   leira.superficie_ha or cultivo.superficie_ha))
    assert horta_id is not None
    return horta_id, validas


def superficie_total(superficies: list[float | None]) -> float | None:
    """A suma das superficies, ou None se falta algunha."""
    if any(s is None for s in superficies):
        return None
    return sum(s for s in superficies if s is not None)
