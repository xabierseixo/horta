"""Comprobación de traballos que a lei obriga a conservar antes de borrar explotacións,
parcelas ou cultivos (RD 1311/2012, RD 1051/2022, RD 787/2023, CUE/SIEX)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import Session

from horta.db import Base
import horta.models  # noqa: F401
from horta.models.analise import Analise
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta
from horta.models.lote import Clasificacion, LoteSaida, Mestura, Transformacion
from horta.models.movemento_animal import MovementoAnimal
from horta.models.outro_traballo import OutroTraballo
from horta.models.parcela import Parcela
from horta.models.producion_animal import ProducionAnimal
from horta.models.traballo import ParteComun
from horta.services.errors import OperacionNonPermitidaError

# Modelos con ParteComun que non son traballos con obriga legal de conservación
# na explotación nin na parcela/cultivo (análises e mantemento común).
_EXCLUIDOS_GLOBAL = {OutroTraballo, Analise}

# Modelos que dependen da explotación e se eliminan con ela cando non hai traballos regulados.
_EXCLUIDOS_HORTA = {
    OutroTraballo,
    Analise,
    Colleita,
    LoteSaida,
    Clasificacion,
    Mestura,
    Transformacion,
}

_DESCRICIONS: dict[str, str] = {
    "TratamentoFito": "tratamentos fitosanitarios rexistrados",
    "TratamentoInstalacion": "tratamentos fitosanitarios rexistrados",
    "Abonado": "abonados rexistrados",
    "Rega": "regas rexistradas",
    "Labor": "labores rexistrados",
    "CoidadoAnimal": "coidados de animais rexistrados",
    "MovementoAnimal": "entradas e saídas de animais rexistradas",
    "ProducionAnimal": "produción dos animais rexistrada",
    "Pastoreo": "pastoreos rexistrados",
    "EntradaProduto": "compras de produtos rexistradas",
    "Colleita": "colleitas rexistradas",
}


def _modelos_con_parte_comun() -> list[type[Any]]:
    return [m.class_ for m in Base.registry.mappers if issubclass(m.class_, ParteComun)]


def _descricion_rexistro(modelo: type[Any]) -> str:
    return _DESCRICIONS.get(modelo.__name__, f"rexistros de {modelo.__name__.lower()}")


def _mensaxe_erro(entidade: Horta | Parcela | Cultivo, modelo: type[Any]) -> str:
    desc = _descricion_rexistro(modelo)
    if isinstance(entidade, Cultivo):
        obriga = " e debe conservarse" if modelo is Colleita else " e debe conservarse (obriga legal)"
        return f"Este cultivo ten {desc}{obriga}. Podes marcalo como rematado."
    elif isinstance(entidade, Parcela):
        return f"Esta parcela ten {desc} e debe conservarse (obriga legal)."
    else:
        obriga = (
            " e debe conservarse."
            if modelo is ProducionAnimal
            else " e debe conservarse (obriga legal)."
        )
        return f"Esta explotación ten {desc}{obriga}"


def _cultivo_ten_rexistros(session: Session, cultivo_id: int, modelo: type[Any]) -> bool:
    if hasattr(modelo, "__table__") and "cultivo_id" in modelo.__table__.c:
        if session.query(modelo).filter_by(cultivo_id=cultivo_id).first() is not None:
            return True
    mapper = inspect(modelo)
    for rel in mapper.relationships:
        target = rel.mapper.class_
        if hasattr(target, "__table__") and "cultivo_id" in target.__table__.c:
            if session.query(target).filter_by(cultivo_id=cultivo_id).first() is not None:
                return True
    return False


def _parcela_ten_rexistros(session: Session, parcela_id: int, modelo: type[Any]) -> bool:
    if hasattr(modelo, "__table__") and "parcela_id" in modelo.__table__.c:
        if session.query(modelo).filter_by(parcela_id=parcela_id).first() is not None:
            return True
    ids_cultivos = [
        c_id
        for (c_id,) in session.query(Cultivo.id).filter_by(parcela_id=parcela_id).all()
    ]
    if ids_cultivos:
        if hasattr(modelo, "__table__") and "cultivo_id" in modelo.__table__.c:
            if session.query(modelo).filter(modelo.cultivo_id.in_(ids_cultivos)).first() is not None:
                return True
        mapper = inspect(modelo)
        for rel in mapper.relationships:
            target = rel.mapper.class_
            if hasattr(target, "__table__") and "cultivo_id" in target.__table__.c:
                if session.query(target).filter(target.cultivo_id.in_(ids_cultivos)).first() is not None:
                    return True
    return False


def _horta_ten_rexistros(session: Session, horta_id: int, modelo: type[Any]) -> bool:
    if hasattr(modelo, "__table__") and "horta_id" in modelo.__table__.c:
        if modelo is MovementoAnimal:
            if (
                session.query(MovementoAnimal)
                .filter(
                    MovementoAnimal.horta_id == horta_id,
                    MovementoAnimal.tipo != "inicial",
                )
                .first()
                is not None
            ):
                return True
        else:
            if session.query(modelo).filter_by(horta_id=horta_id).first() is not None:
                return True
    return False


def _hai_rexistros_que_conservar(
    session: Session, entidade: Horta | Parcela | Cultivo, modelo: type[Any]
) -> bool:
    if modelo in _EXCLUIDOS_GLOBAL:
        return False
    if isinstance(entidade, Cultivo):
        return _cultivo_ten_rexistros(session, entidade.id, modelo)
    elif isinstance(entidade, Parcela):
        return _parcela_ten_rexistros(session, entidade.id, modelo)
    elif isinstance(entidade, Horta):
        if modelo in _EXCLUIDOS_HORTA:
            return False
        return _horta_ten_rexistros(session, entidade.id, modelo)
    return False


def comprobar_conservar(session: Session, entidade: Horta | Parcela | Cultivo) -> None:
    """Comproba se hai traballos regulados que obriguen a conservar a entidade (explotación,
    parcela ou cultivo).

    Recorre os modelos con parte común (e as colleitas nos cultivos e parcelas)
    e lanza OperacionNonPermitidaError coa mensaxe legal correspondente se hai rexistros
    que impidan o borrado.
    """
    for modelo in _modelos_con_parte_comun():
        if _hai_rexistros_que_conservar(session, entidade, modelo):
            raise OperacionNonPermitidaError(_mensaxe_erro(entidade, modelo))
