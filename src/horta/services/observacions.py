"""Observacións e limiares de pragas, enfermidades e malas herbas (GIP)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.observacion import LimiarPraga, ObservacionPraga
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

TIPOS_PROBLEMA = {"praga", "enfermidade", "mala_herba"}

METODOS: dict[str, str] = {
    "trampa": "Trampa",
    "mostraxe": "Mostraxe",
    "sintomas": "Síntomas",
}

UNIDADES_CONTO: dict[str, str] = {
    "capturas por trampa": "Capturas por trampa",
    "% de plantas": "% de plantas",
    "% de follas": "% de follas",
    "individuos por planta": "Individuos por planta",
    "outro": "Outro",
}

NIVEIS: dict[str, str] = {
    "sen": "Sen",
    "baixo": "Baixo",
    "medio": "Medio",
    "alto": "Alto",
}

_SEN_CAMBIO: Any = object()


def _validar_observacion(
    session: Session,
    horta_id: int,
    cultivo_id: int,
    data: date,
    problema_tipo: str,
    problema_codigo: str,
    metodo: str,
    conto: float | None,
    unidade_conto: str | None,
    nivel: str | None,
    estado_fenoloxico: str | None,
    persoa_id: int | None,
) -> None:
    cultivo = session.get(Cultivo, cultivo_id)
    parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
    if cultivo is None or parcela is None or parcela.horta_id != horta_id:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    if problema_tipo not in TIPOS_PROBLEMA:
        raise OperacionNonPermitidaError(f"Tipo de problema descoñecido: {problema_tipo}")
    validar_codigo(session, problema_tipo, problema_codigo, data)
    if metodo not in METODOS:
        raise OperacionNonPermitidaError(f"Método de observación non válido: {metodo}")
    if conto is None and (nivel is None or not str(nivel).strip()):
        raise OperacionNonPermitidaError("Indica o conto ou o nivel da observación")
    if conto is not None:
        if not unidade_conto or unidade_conto not in UNIDADES_CONTO:
            raise OperacionNonPermitidaError("Indica a unidade de conto da observación")
        if conto < 0:
            raise OperacionNonPermitidaError("O conto non pode ser negativo")
    if nivel is not None and str(nivel).strip() and nivel not in NIVEIS:
        raise OperacionNonPermitidaError(f"Nivel de observación non válido: {nivel}")
    if estado_fenoloxico:
        validar_codigo(session, "estado_fenoloxico", estado_fenoloxico, data)
    comprobar_quen(session, horta_id, persoa_id, None)


def crear_observacion(
    session: Session,
    actor: Usuario,
    horta_id: int,
    *,
    cultivo_id: int,
    data: date,
    problema_tipo: str,
    problema_codigo: str,
    metodo: str,
    conto: float | None = None,
    unidade_conto: str | None = None,
    nivel: str | None = None,
    estado_fenoloxico: str | None = None,
    notas: str | None = None,
    persoa_id: int | None = None,
) -> ObservacionPraga:
    """Rexistra unha nova observación de pragas nun cultivo da explotación."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar_observacion(
        session,
        horta_id,
        cultivo_id,
        data,
        problema_tipo,
        problema_codigo,
        metodo,
        conto,
        unidade_conto,
        nivel,
        estado_fenoloxico,
        persoa_id,
    )
    obs = ObservacionPraga(
        horta_id=horta_id,
        cultivo_id=cultivo_id,
        data=data,
        problema_tipo=problema_tipo,
        problema_codigo=problema_codigo,
        metodo=metodo,
        conto=conto,
        unidade_conto=unidade_conto if conto is not None else None,
        nivel=nivel,
        estado_fenoloxico=estado_fenoloxico or None,
        notas=notas.strip() if notas and notas.strip() else None,
        persoa_id=persoa_id,
        creado_por=actor.id,
    )
    session.add(obs)
    session.commit()
    return obs


def actualizar_observacion(
    session: Session,
    actor: Usuario,
    observacion: ObservacionPraga,
    *,
    cultivo_id: int | None = None,
    data: date | None = None,
    problema_tipo: str | None = None,
    problema_codigo: str | None = None,
    metodo: str | None = None,
    conto: float | None = _SEN_CAMBIO,
    unidade_conto: str | None = _SEN_CAMBIO,
    nivel: str | None = _SEN_CAMBIO,
    estado_fenoloxico: str | None = _SEN_CAMBIO,
    notas: str | None = _SEN_CAMBIO,
    persoa_id: int | None = _SEN_CAMBIO,
    **kwargs: Any,
) -> ObservacionPraga:
    """Actualiza os datos dunha observación vixente."""
    if observacion.baixa:
        raise OperacionNonPermitidaError("Unha observación dada de baixa non se pode modificar")
    comprobar_rol_horta(session, observacion.horta_id, actor, _ROLES_ESCRITURA)

    novo_cultivo_id = cultivo_id if cultivo_id is not None else observacion.cultivo_id
    nova_data = data if data is not None else observacion.data
    novo_problema_tipo = (
        problema_tipo if problema_tipo is not None else observacion.problema_tipo
    )
    novo_problema_codigo = (
        problema_codigo if problema_codigo is not None else observacion.problema_codigo
    )
    novo_metodo = metodo if metodo is not None else observacion.metodo
    novo_conto = observacion.conto if conto is _SEN_CAMBIO else conto
    nova_unidade_conto = (
        observacion.unidade_conto if unidade_conto is _SEN_CAMBIO else unidade_conto
    )
    novo_nivel = observacion.nivel if nivel is _SEN_CAMBIO else nivel
    novo_estado = (
        observacion.estado_fenoloxico if estado_fenoloxico is _SEN_CAMBIO else estado_fenoloxico
    )
    novas_notas = (
        observacion.notas
        if notas is _SEN_CAMBIO
        else (notas.strip() if notas and notas.strip() else None)
    )
    nova_persoa = observacion.persoa_id if persoa_id is _SEN_CAMBIO else persoa_id

    _validar_observacion(
        session,
        observacion.horta_id,
        novo_cultivo_id,
        nova_data,
        novo_problema_tipo,
        novo_problema_codigo,
        novo_metodo,
        novo_conto,
        nova_unidade_conto,
        novo_nivel,
        novo_estado,
        nova_persoa,
    )

    observacion.cultivo_id = novo_cultivo_id
    observacion.data = nova_data
    observacion.problema_tipo = novo_problema_tipo
    observacion.problema_codigo = novo_problema_codigo
    observacion.metodo = novo_metodo
    observacion.conto = novo_conto
    observacion.unidade_conto = nova_unidade_conto if novo_conto is not None else None
    observacion.nivel = novo_nivel
    observacion.estado_fenoloxico = novo_estado or None
    observacion.notas = novas_notas
    observacion.persoa_id = nova_persoa
    session.commit()
    return observacion


def dar_de_baixa_observacion(
    session: Session, actor: Usuario, observacion: ObservacionPraga
) -> None:
    """Dá de baixa lóxica unha observación."""
    comprobar_rol_horta(session, observacion.horta_id, actor, _ROLES_ESCRITURA)
    observacion.baixa = True
    session.commit()


def listar_observacions(
    session: Session,
    actor: Usuario,
    horta_id: int,
    cultivo_id: int | None = None,
    desde: date | None = None,
    ata: date | None = None,
) -> list[ObservacionPraga]:
    """Lista observacións non dadas de baixa, das máis novas ás máis vellas."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(ObservacionPraga).filter(
        ObservacionPraga.horta_id == horta_id,
        ObservacionPraga.baixa.is_(False),
    )
    if cultivo_id is not None:
        consulta = consulta.filter(ObservacionPraga.cultivo_id == cultivo_id)
    if desde is not None:
        consulta = consulta.filter(ObservacionPraga.data >= desde)
    if ata is not None:
        consulta = consulta.filter(ObservacionPraga.data <= ata)
    return list(
        consulta.order_by(ObservacionPraga.data.desc(), ObservacionPraga.id.desc()).all()
    )


def gardar_limiar(
    session: Session,
    actor: Usuario,
    horta_id: int,
    problema_tipo: str,
    problema_codigo: str,
    metodo: str,
    unidade_conto: str,
    valor: float,
    fonte: str,
    cultivo_siex_codigo: int | None = None,
    limiar_id: int | None = None,
) -> LimiarPraga:
    """Garda ou actualiza un limiar de intervención oficial (GIP)."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not fonte or not fonte.strip():
        raise OperacionNonPermitidaError("A fonte do limiar é obrigatoria")
    if problema_tipo not in TIPOS_PROBLEMA:
        raise OperacionNonPermitidaError(f"Tipo de problema descoñecido: {problema_tipo}")
    if metodo not in METODOS:
        raise OperacionNonPermitidaError(f"Método de observación non válido: {metodo}")
    if unidade_conto not in UNIDADES_CONTO:
        raise OperacionNonPermitidaError(f"Unidade de conto non válida: {unidade_conto}")
    if valor is None or valor < 0:
        raise OperacionNonPermitidaError("O valor do limiar non pode ser negativo")

    limiar: LimiarPraga | None = None
    if limiar_id is not None:
        limiar = session.get(LimiarPraga, limiar_id)
        if limiar is None or limiar.horta_id != horta_id:
            raise OperacionNonPermitidaError("O limiar indicado non existe")
        limiar.cultivo_siex_codigo = cultivo_siex_codigo
        limiar.problema_tipo = problema_tipo
        limiar.problema_codigo = problema_codigo
        limiar.metodo = metodo
        limiar.unidade_conto = unidade_conto
        limiar.valor = float(valor)
        limiar.fonte = fonte.strip()
        limiar.baixa = False
    else:
        existente = (
            session.query(LimiarPraga)
            .filter(
                LimiarPraga.horta_id == horta_id,
                LimiarPraga.cultivo_siex_codigo == cultivo_siex_codigo,
                LimiarPraga.problema_tipo == problema_tipo,
                LimiarPraga.problema_codigo == problema_codigo,
                LimiarPraga.metodo == metodo,
                LimiarPraga.unidade_conto == unidade_conto,
                LimiarPraga.baixa.is_(False),
            )
            .first()
        )
        if existente is not None:
            existente.valor = float(valor)
            existente.fonte = fonte.strip()
            limiar = existente
        else:
            limiar = LimiarPraga(
                horta_id=horta_id,
                cultivo_siex_codigo=cultivo_siex_codigo,
                problema_tipo=problema_tipo,
                problema_codigo=problema_codigo,
                metodo=metodo,
                unidade_conto=unidade_conto,
                valor=float(valor),
                fonte=fonte.strip(),
                baixa=False,
            )
            session.add(limiar)

    session.commit()
    return limiar


def listar_limiares(
    session: Session,
    actor: Usuario,
    horta_id: int,
    cultivo_siex_codigo: int | None = None,
) -> list[LimiarPraga]:
    """Lista os limiares vixentes dunha explotación."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(LimiarPraga).filter(
        LimiarPraga.horta_id == horta_id,
        LimiarPraga.baixa.is_(False),
    )
    if cultivo_siex_codigo is not None:
        consulta = consulta.filter(LimiarPraga.cultivo_siex_codigo == cultivo_siex_codigo)
    return list(
        consulta.order_by(
            LimiarPraga.problema_tipo, LimiarPraga.problema_codigo, LimiarPraga.id
        ).all()
    )


def dar_de_baixa_limiar(session: Session, actor: Usuario, limiar: LimiarPraga) -> None:
    """Dá de baixa lóxica un limiar."""
    comprobar_rol_horta(session, limiar.horta_id, actor, _ROLES_ESCRITURA)
    limiar.baixa = True
    session.commit()


def limiar_para(
    session: Session,
    horta_id: int,
    cultivo: Cultivo | int | None,
    problema_tipo: str,
    problema_codigo: str,
    metodo: str,
    unidade_conto: str,
) -> LimiarPraga | None:
    """Obtén o limiar específico do cultivo ou, se non o hai, o limiar xeral."""
    siex_codigo: int | None = None
    if isinstance(cultivo, Cultivo):
        siex_codigo = cultivo.cultivo_siex_codigo
    elif isinstance(cultivo, int):
        c = session.get(Cultivo, cultivo)
        siex_codigo = c.cultivo_siex_codigo if c is not None else cultivo

    if siex_codigo is not None:
        especifico = (
            session.query(LimiarPraga)
            .filter(
                LimiarPraga.horta_id == horta_id,
                LimiarPraga.cultivo_siex_codigo == siex_codigo,
                LimiarPraga.problema_tipo == problema_tipo,
                LimiarPraga.problema_codigo == problema_codigo,
                LimiarPraga.metodo == metodo,
                LimiarPraga.unidade_conto == unidade_conto,
                LimiarPraga.baixa.is_(False),
            )
            .order_by(LimiarPraga.id.desc())
            .first()
        )
        if especifico is not None:
            return especifico

    xeral = (
        session.query(LimiarPraga)
        .filter(
            LimiarPraga.horta_id == horta_id,
            LimiarPraga.cultivo_siex_codigo.is_(None),
            LimiarPraga.problema_tipo == problema_tipo,
            LimiarPraga.problema_codigo == problema_codigo,
            LimiarPraga.metodo == metodo,
            LimiarPraga.unidade_conto == unidade_conto,
            LimiarPraga.baixa.is_(False),
        )
        .order_by(LimiarPraga.id.desc())
        .first()
    )
    return xeral


def supera_limiar(obs: ObservacionPraga | Any, limiar: LimiarPraga | Any) -> bool:
    """Función pura: devolve True se o conto da observación é maior ou igual ca o valor."""
    if obs is None or limiar is None:
        return False
    conto = getattr(obs, "conto", None)
    valor = getattr(limiar, "valor", None)
    if conto is None or valor is None:
        return False
    return float(conto) >= float(valor)
