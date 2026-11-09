"""Servizo de estimacións da colleita antes da recollida."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.estimacion import EstimacionColleita
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.colleitas import rendemento_kg_ha
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def kg_ha_por_mostraxe(
    plantas_ha: float, unidades_planta: float, peso_unidade_g: float
) -> float:
    """Cálculo de kg/ha por mostraxe: plantas × unidades × peso / 1000 (redondeado a 1 decimal)."""
    if plantas_ha <= 0 or unidades_planta <= 0 or peso_unidade_g <= 0:
        raise OperacionNonPermitidaError("Os datos de mostraxe teñen que ser maiores que 0")
    return round(plantas_ha * unidades_planta * peso_unidade_g / 1000.0, 1)


def _cultivo_e_horta(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    if horta_id is None:
        raise OperacionNonPermitidaError("A parcela deste cultivo non existe")
    return cultivo, horta_id


def crear_estimacion(
    session: Session,
    actor: Usuario,
    cultivo_id: int,
    data: date,
    metodo: str,
    kg_ha: float | None = None,
    plantas_ha: float | None = None,
    unidades_planta: float | None = None,
    peso_unidade_g: float | None = None,
    notas: str | None = None,
) -> EstimacionColleita:
    """Crea unha estimación de colleita (por mostraxe ou directa)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)

    if metodo not in ("mostraxe", "directa"):
        raise OperacionNonPermitidaError(
            f"Método non válido: «{metodo}». Ten que ser «mostraxe» ou «directa»"
        )

    if metodo == "mostraxe":
        if plantas_ha is None or plantas_ha <= 0:
            raise OperacionNonPermitidaError(
                "As plantas por hectárea son obrigatorias e teñen que ser maiores que 0"
            )
        if unidades_planta is None or unidades_planta <= 0:
            raise OperacionNonPermitidaError(
                "As unidades por planta son obrigatorias e teñen que ser maiores que 0"
            )
        if peso_unidade_g is None or peso_unidade_g <= 0:
            raise OperacionNonPermitidaError(
                "O peso por unidade en gramos é obrigatorio e ten que ser maior que 0"
            )
        kg_ha_calculado = kg_ha_por_mostraxe(plantas_ha, unidades_planta, peso_unidade_g)
        plantas_ha_val = float(plantas_ha)
        unidades_planta_val = float(unidades_planta)
        peso_unidade_g_val = float(peso_unidade_g)
    else:
        if kg_ha is None or kg_ha <= 0:
            raise OperacionNonPermitidaError(
                "A cantidade estimada en kg/ha é obrigatoria e ten que ser maior que 0"
            )
        kg_ha_calculado = round(float(kg_ha), 1)
        plantas_ha_val = None
        unidades_planta_val = None
        peso_unidade_g_val = None

    estimacion = EstimacionColleita(
        cultivo_id=cultivo_id,
        data=data,
        metodo=metodo,
        plantas_ha=plantas_ha_val,
        unidades_planta=unidades_planta_val,
        peso_unidade_g=peso_unidade_g_val,
        kg_ha=kg_ha_calculado,
        notas=notas.strip() if (notas and notas.strip()) else None,
    )
    session.add(estimacion)
    session.commit()
    return estimacion


def listar_estimacions(
    session: Session, actor: Usuario, cultivo_id: int
) -> list[EstimacionColleita]:
    """Lista as estimacións dun cultivo ordenadas da máis recente á máis antiga."""
    _, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(EstimacionColleita)
        .filter(EstimacionColleita.cultivo_id == cultivo_id)
        .order_by(EstimacionColleita.data.desc(), EstimacionColleita.id.desc())
        .all()
    )


def borrar_estimacion(session: Session, actor: Usuario, estimacion_id: int) -> None:
    """Borra unha estimación da colleita."""
    estimacion = session.get(EstimacionColleita, estimacion_id)
    if estimacion is None:
        raise OperacionNonPermitidaError("Esa estimación non existe")
    _, horta_id = _cultivo_e_horta(session, estimacion.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    session.delete(estimacion)
    session.commit()


@dataclass
class ResumoEstimacion:
    obxectivo_kg_ha: float | None = None
    estimado_kg_ha: float | None = None
    estimado_total_kg: float | None = None
    colleitado_kg_ha: float | None = None
    porcentaxe_colleitada: float | None = None


def resumo_estimacion(
    session: Session, actor: Usuario, cultivo_id: int
) -> ResumoEstimacion:
    """Resumo comparativo da colleita estimada fronte ao obxectivo e ao colleitado real."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)

    estimacions = listar_estimacions(session, actor, cultivo_id)
    estimado_kg_ha = estimacions[0].kg_ha if estimacions else None

    estimado_total_kg = (
        round(estimado_kg_ha * cultivo.superficie_ha, 1)
        if (estimado_kg_ha is not None and cultivo.superficie_ha is not None)
        else None
    )

    colleitado_kg_ha = rendemento_kg_ha(session, actor, cultivo_id)

    porcentaxe_colleitada = (
        round(colleitado_kg_ha / estimado_kg_ha * 100, 0)
        if (
            colleitado_kg_ha is not None
            and estimado_kg_ha is not None
            and estimado_kg_ha > 0
        )
        else None
    )

    return ResumoEstimacion(
        obxectivo_kg_ha=cultivo.obxectivo_colleita_kg_ha,
        estimado_kg_ha=estimado_kg_ha,
        estimado_total_kg=estimado_total_kg,
        colleitado_kg_ha=colleitado_kg_ha,
        porcentaxe_colleitada=porcentaxe_colleitada,
    )
