"""Servizo de visitas de campo do persoal asesor técnico (mellora N7)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.models.visita import VisitaCampo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

_OMITIDO = object()


def _validar_datos_visita(
    session: Session,
    horta_id: int,
    asesor_persoa_id: int,
    data: date,
    cultivos: Sequence[int],
    proxima_visita: date | None = None,
) -> None:
    asesor = session.get(Persoa, asesor_persoa_id)
    if asesor is None or asesor.horta_id != horta_id or not asesor.ten_papel("asesor"):
        raise OperacionNonPermitidaError("Escolle unha persoa asesora da explotación")

    for cid in cultivos:
        cultivo = session.get(Cultivo, cid)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None or parcela.horta_id != horta_id:
            raise OperacionNonPermitidaError(
                "O cultivo indicado non pertence a esta explotación"
            )

    if proxima_visita is not None and proxima_visita < data:
        raise OperacionNonPermitidaError(
            "A data da próxima visita non pode ser anterior á data da visita"
        )


def crear_visita(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    asesor_persoa_id: int,
    data: date,
    cultivos: list[int] | None = None,
    hora_inicio: time | None = None,
    estado_xeral: str | None = None,
    conclusions: str | None = None,
    proxima_visita: date | None = None,
) -> VisitaCampo:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    lista_cultivos: list[int] = list(cultivos) if cultivos else []
    _validar_datos_visita(
        session,
        horta_id,
        asesor_persoa_id,
        data,
        lista_cultivos,
        proxima_visita,
    )
    visita = VisitaCampo(
        horta_id=horta_id,
        asesor_persoa_id=asesor_persoa_id,
        data=data,
        hora_inicio=hora_inicio,
        cultivos=lista_cultivos,
        estado_xeral=estado_xeral.strip() if estado_xeral and estado_xeral.strip() else None,
        conclusions=conclusions.strip() if conclusions and conclusions.strip() else None,
        proxima_visita=proxima_visita,
        baixa=False,
        creado_por=actor.id if actor else None,
    )
    session.add(visita)
    session.commit()
    return visita


def actualizar_visita(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
    *,
    asesor_persoa_id: int | None = None,
    data: date | None = None,
    hora_inicio: Any = _OMITIDO,
    cultivos: list[int] | None = None,
    estado_xeral: Any = _OMITIDO,
    conclusions: Any = _OMITIDO,
    proxima_visita: Any = _OMITIDO,
) -> VisitaCampo:
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v

    if visita.baixa:
        raise OperacionNonPermitidaError(
            "Unha visita dada de baixa non se pode modificar"
        )
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)

    novo_asesor = (
        asesor_persoa_id if asesor_persoa_id is not None else visita.asesor_persoa_id
    )
    nova_data = data if data is not None else visita.data
    novos_cultivos = (
        list(cultivos) if cultivos is not None else list(visita.cultivos or [])
    )
    nova_hora = visita.hora_inicio if hora_inicio is _OMITIDO else hora_inicio
    novo_estado_xeral = (
        visita.estado_xeral if estado_xeral is _OMITIDO else estado_xeral
    )
    novas_conclusions = (
        visita.conclusions if conclusions is _OMITIDO else conclusions
    )
    nova_proxima_visita = (
        visita.proxima_visita if proxima_visita is _OMITIDO else proxima_visita
    )

    _validar_datos_visita(
        session,
        visita.horta_id,
        novo_asesor,
        nova_data,
        novos_cultivos,
        nova_proxima_visita,
    )

    visita.asesor_persoa_id = novo_asesor
    visita.data = nova_data
    visita.cultivos = novos_cultivos
    visita.hora_inicio = nova_hora
    visita.estado_xeral = (
        novo_estado_xeral.strip()
        if novo_estado_xeral and isinstance(novo_estado_xeral, str) and novo_estado_xeral.strip()
        else (novo_estado_xeral if novo_estado_xeral is None else str(novo_estado_xeral))
    )
    visita.conclusions = (
        novas_conclusions.strip()
        if novas_conclusions and isinstance(novas_conclusions, str) and novas_conclusions.strip()
        else (novas_conclusions if novas_conclusions is None else str(novas_conclusions))
    )
    visita.proxima_visita = nova_proxima_visita

    session.commit()
    return visita


def dar_de_baixa_visita(
    session: Session,
    actor: Usuario,
    visita: VisitaCampo | int,
) -> None:
    if isinstance(visita, int):
        v = session.get(VisitaCampo, visita)
        if v is None:
            raise OperacionNonPermitidaError("Non existe a visita")
        visita = v
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_ESCRITURA)
    visita.baixa = True
    session.commit()


def listar_visitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    desde: date | None = None,
    ata: date | None = None,
) -> list[VisitaCampo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(VisitaCampo).filter_by(horta_id=horta_id, baixa=False)
    if desde is not None:
        consulta = consulta.filter(VisitaCampo.data >= desde)
    if ata is not None:
        consulta = consulta.filter(VisitaCampo.data <= ata)
    return list(
        consulta.order_by(VisitaCampo.data.desc(), VisitaCampo.id.desc()).all()
    )


def proximas_visitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    hoxe: date | None = None,
    dias: int = 14,
) -> list[VisitaCampo]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    data_actual = hoxe or date.today()
    limite = data_actual + timedelta(days=dias)
    return list(
        session.query(VisitaCampo)
        .filter(
            VisitaCampo.horta_id == horta_id,
            VisitaCampo.baixa.is_(False),
            VisitaCampo.proxima_visita.is_not(None),
            VisitaCampo.proxima_visita >= data_actual,
            VisitaCampo.proxima_visita <= limite,
        )
        .order_by(VisitaCampo.proxima_visita.asc(), VisitaCampo.id.asc())
        .all()
    )


def obter_visita(
    session: Session,
    actor: Usuario,
    visita_id: int,
) -> VisitaCampo | None:
    visita = session.get(VisitaCampo, visita_id)
    if visita is None or visita.baixa:
        return None
    comprobar_rol_horta(session, visita.horta_id, actor, _ROLES_LECTURA)
    return visita


__all__ = [
    "actualizar_visita",
    "crear_visita",
    "dar_de_baixa_visita",
    "listar_visitas",
    "obter_visita",
    "proximas_visitas",
]
