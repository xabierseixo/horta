from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.maquina import Maquina
from horta.models.tratamento_fito import TratamentoAplicador, TratamentoFito
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_IDENTIFICADORES = ("num_roma", "num_reganip", "id_equipo_non_inscribible")

CAMPOS_EDITABLES_MAQUINA = frozenset(
    {"alias", "tipo_une", "marca_modelo", "num_roma", "num_reganip", "id_equipo_non_inscribible",
     "propia", "potencia", "unidade_potencia", "tipo_enerxia", "data_ultima_inspeccion", "alugada",
     "activa", "data_adquisicion", "custo_hora"}
)


def comprobar_maquina(session: Session, horta_id: int, maquina_id: int | None) -> None:
    """A máquina dun traballo (opcional) ten que ser da mesma explotación."""
    if maquina_id is None:
        return
    maquina = session.get(Maquina, maquina_id)
    if maquina is None or maquina.horta_id != horta_id:
        raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")


def maquinas_de_tratamento(session: Session, horta_id: int) -> set[int]:
    """As máquinas usadas nalgún tratamento fitosanitario da explotación."""
    return {m for (m,) in session.query(TratamentoAplicador.maquina_id)
            .join(TratamentoFito, TratamentoFito.id == TratamentoAplicador.tratamento_id)
            .filter(TratamentoFito.horta_id == horta_id,
                    TratamentoAplicador.maquina_id.is_not(None))}


def _mais_anos(data: date, anos: int) -> date:
    try:
        return data.replace(year=data.year + anos)
    except ValueError:  # 29 de febreiro
        return data.replace(year=data.year + anos, day=28)


def aviso_inspeccion(maquina: Maquina, hoxe: date | None = None) -> str | None:
    """Equipos de tratamento (RD 1702/2011 art. 5): inspección cada 3 anos desde 2020; os
    novos, a primeira dentro dos 5 primeiros anos. As mochilas e carretillas pequenas, que
    non se inscriben no ROMA, quedan fóra (art. 3.2). Só avisa."""
    if maquina.id_equipo_non_inscribible or not maquina.activa:
        return None
    hoxe = hoxe or date.today()
    if maquina.data_ultima_inspeccion is not None:
        limite = _mais_anos(maquina.data_ultima_inspeccion, 3)
        return f"Inspección vencida o {limite:%d/%m/%Y}" if hoxe > limite else None
    if maquina.data_adquisicion is not None:
        limite = _mais_anos(maquina.data_adquisicion, 5)
        if hoxe <= limite:
            return None
        return f"Primeira inspección vencida o {limite:%d/%m/%Y}"
    return "Sen inspección apuntada"


def _validar(datos: dict[str, Any]) -> None:
    if datos.get("custo_hora") is not None and datos["custo_hora"] < 0:
        raise OperacionNonPermitidaError("O custo da hora non pode ser negativo")
    if sum(1 for c in _IDENTIFICADORES if datos.get(c)) > 1:
        raise OperacionNonPermitidaError(
            "Indica só un identificador: nº ROMA, nº REGANIP ou identificador do equipo"
        )


def crear_maquina(
    session: Session, actor: Usuario, horta_id: int, alias: str, **campos: Any
) -> Maquina:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(campos)
    maquina = Maquina(horta_id=horta_id, alias=alias, **campos)
    session.add(maquina)
    session.commit()
    return maquina


def actualizar_maquina(
    session: Session, actor: Usuario, maquina: Maquina, **cambios: Any
) -> Maquina:
    non_editables = set(cambios) - CAMPOS_EDITABLES_MAQUINA
    if non_editables:
        raise ValueError(f"Campos non editables nunha máquina: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, maquina.horta_id, actor, _ROLES_ESCRITURA)
    _validar({c: getattr(maquina, c) for c in _IDENTIFICADORES} | cambios)
    for campo, valor in cambios.items():
        setattr(maquina, campo, valor)
    session.commit()
    return maquina


def listar_maquinas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Maquina]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Maquina).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Maquina.alias).all())
