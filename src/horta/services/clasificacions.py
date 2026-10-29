"""Clasificación e mestura de lotes: dous traballos
coa parte común. Clasificar reparte un lote por clases sen cambiar de lote (a clase é un dato
da partida); o refugo conta como perda. Mesturar xunta lotes nun lote novo que garda as súas
orixes (Directiva 2011/91/UE; FSMA 204: o resultado leva un lote novo ligado aos de orixe)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.lote import Clasificacion, ClasificacionClase, Lote, Mestura, MesturaOrixe
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import (
    clases_da_ficha,
    codigo_por_agrupacion,
    ficha_do_lote,
    queda_por_clase,
)
from horta.services.maquinaria import comprobar_maquina
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


def _lote(session: Session, lote_id: int) -> Lote:
    lote = session.get(Lote, lote_id)
    if lote is None or lote.baixa:
        raise OperacionNonPermitidaError("Ese lote non existe")
    return lote


def _comun(session: Session, horta_id: int, data: date, hoxe: date, persoa_id: int | None,
           horas: float | None, maquina_id: int | None) -> None:
    if data > hoxe:
        raise OperacionNonPermitidaError("A data non pode ser futura")
    comprobar_quen(session, horta_id, persoa_id, horas)
    comprobar_maquina(session, horta_id, maquina_id)


# --- Clasificación

@dataclass(kw_only=True)
class DatosClasificacion:
    lote_id: int
    data: date
    # clase → cantidade, na unidade do lote
    clases: dict[str, float]
    refugo: float = 0
    persoa_id: int | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def _validar_clasificacion(session: Session, datos: DatosClasificacion, lote: Lote,
                           hoxe: date, excepto_id: int | None) -> None:
    _comun(session, lote.horta_id, datos.data, hoxe, datos.persoa_id, datos.horas,
           datos.maquina_id)
    if datos.data < lote.data:
        raise OperacionNonPermitidaError(
            f"O lote empezou o {lote.data:%d/%m/%Y}: a clasificación non pode ser anterior")
    clases = {c.strip(): v for c, v in datos.clases.items() if c.strip() and v}
    if not clases:
        raise OperacionNonPermitidaError("Indica canto saíu de polo menos unha clase")
    if any(v < 0 for v in clases.values()) or datos.refugo < 0:
        raise OperacionNonPermitidaError("As cantidades non poden ser negativas")
    permitidas = clases_da_ficha(ficha_do_lote(session, lote))
    if permitidas and set(clases) - set(permitidas):
        raise OperacionNonPermitidaError(
            f"Clases deste produto: {', '.join(permitidas)}. Engade as novas na súa ficha")
    sen_clasificar = queda_por_clase(session, lote, excepto_clasificacion=excepto_id)[None]
    total = sum(clases.values()) + datos.refugo
    if total > sen_clasificar + 1e-9:
        raise OperacionNonPermitidaError(
            f"Do lote {lote.codigo} só quedan {sen_clasificar:g} {lote.unidade} sen clasificar")


def _copiar_clasificacion(cl: Clasificacion, datos: DatosClasificacion, lote: Lote) -> None:
    cl.horta_id = lote.horta_id
    cl.lote_id = lote.id
    cl.data = datos.data
    cl.refugo = datos.refugo or 0
    cl.clases = [ClasificacionClase(clase=c.strip(), cantidade=v)
                 for c, v in datos.clases.items() if c.strip() and v]
    cl.persoa_id = datos.persoa_id
    cl.horas = datos.horas
    cl.maquina_id = datos.maquina_id
    cl.notas = datos.notas or None


def crear_clasificacion(session: Session, actor: Usuario, datos: DatosClasificacion,
                        hoxe: date | None = None) -> Clasificacion:
    lote = _lote(session, datos.lote_id)
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_ESCRITURA)
    _validar_clasificacion(session, datos, lote, hoxe or date.today(), None)
    cl = Clasificacion(creado_por=actor.id)
    _copiar_clasificacion(cl, datos, lote)
    session.add(cl)
    session.commit()
    return cl


def actualizar_clasificacion(session: Session, actor: Usuario, cl: Clasificacion,
                             datos: DatosClasificacion, hoxe: date | None = None
                             ) -> Clasificacion:
    if cl.baixa:
        raise OperacionNonPermitidaError("Unha clasificación dada de baixa non se modifica")
    comprobar_rol_horta(session, cl.horta_id, actor, _ROLES_ESCRITURA)
    if datos.lote_id != cl.lote_id:
        raise OperacionNonPermitidaError("Non se pode cambiar o lote dunha clasificación")
    lote = _lote(session, cl.lote_id)
    _validar_clasificacion(session, datos, lote, hoxe or date.today(), cl.id)
    _comprobar_que_chega(session, lote, cl, datos)
    _copiar_clasificacion(cl, datos, lote)
    session.commit()
    return cl


def _comprobar_que_chega(session: Session, lote: Lote, cl: Clasificacion | None,
                         datos: DatosClasificacion | None) -> None:
    """Ao cambiar ou dar de baixa unha clasificación, o xa vendido de cada clase ten que
    seguir cabendo."""
    queda = queda_por_clase(session, lote, excepto_clasificacion=cl.id if cl else None)
    novas = {c.strip(): v for c, v in (datos.clases if datos else {}).items() if c.strip()}
    for clase, cantidade in queda.items():
        if clase is not None and cantidade + novas.get(clase, 0) < -1e-9:
            raise OperacionNonPermitidaError(
                f"Xa saíron {-cantidade:g} {lote.unidade} de {clase} que viñan desta "
                "clasificación")


def dar_de_baixa_clasificacion(session: Session, actor: Usuario, cl: Clasificacion) -> None:
    comprobar_rol_horta(session, cl.horta_id, actor, _ROLES_ESCRITURA)
    _comprobar_que_chega(session, _lote(session, cl.lote_id), cl, None)
    cl.baixa = True
    session.commit()


def listar_clasificacions(session: Session, actor: Usuario, horta_id: int,
                          lote_id: int | None = None) -> list[Clasificacion]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Clasificacion).filter_by(horta_id=horta_id, baixa=False)
    if lote_id is not None:
        consulta = consulta.filter_by(lote_id=lote_id)
    return list(consulta.order_by(Clasificacion.data.desc(), Clasificacion.id.desc()))


# --- Mestura

@dataclass(kw_only=True)
class OrixeMestura:
    lote_id: int
    cantidade: float
    clase: str | None = None


@dataclass(kw_only=True)
class DatosMestura:
    data: date
    orixes: list[OrixeMestura] = field(default_factory=list)
    codigo: str | None = None  # baleiro: o que toca segundo como se agrupa o produto
    persoa_id: int | None = None
    horas: float | None = None
    maquina_id: int | None = None
    notas: str | None = None


def crear_mestura(session: Session, actor: Usuario, horta_id: int, datos: DatosMestura,
                  hoxe: date | None = None) -> Mestura:
    """Un lote novo cos lotes de orixe. Todos do mesmo produto e coa mesma unidade."""
    from horta.services.lotes import lote_para_entrada

    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _comun(session, horta_id, datos.data, hoxe or date.today(), datos.persoa_id, datos.horas,
           datos.maquina_id)
    if len({o.lote_id for o in datos.orixes}) < 2:
        raise OperacionNonPermitidaError("Escolle polo menos dous lotes para mesturar")
    lotes = [_lote(session, o.lote_id) for o in datos.orixes]
    if any(lt.horta_id != horta_id for lt in lotes):
        raise OperacionNonPermitidaError("Ese lote non é desta explotación")
    if len({lt.produto_venda_id for lt in lotes}) > 1 or len({lt.unidade for lt in lotes}) > 1:
        raise OperacionNonPermitidaError(
            "Só se mesturan lotes do mesmo produto e coa mesma unidade")
    for orixe, lote in zip(datos.orixes, lotes, strict=True):
        if orixe.cantidade is None or orixe.cantidade <= 0:
            raise OperacionNonPermitidaError("Cada cantidade ten que ser maior que 0")
        if datos.data < lote.data:
            raise OperacionNonPermitidaError(
                f"O lote {lote.codigo} empezou o {lote.data:%d/%m/%Y}")
        queda = queda_por_clase(session, lote).get(orixe.clase)
        if queda is None or orixe.cantidade > queda + 1e-9:
            raise OperacionNonPermitidaError(
                f"Do lote {lote.codigo} só quedan {queda or 0:g} {lote.unidade}"
                + (f" de {orixe.clase}" if orixe.clase else ""))
    primeiro = lotes[0]
    ficha = ficha_do_lote(session, primeiro)
    codigo = (datos.codigo or "").strip() or codigo_por_agrupacion(session, ficha, datos.data)
    if codigo in {lt.codigo for lt in lotes}:
        raise OperacionNonPermitidaError("O lote da mestura ten que ser novo")
    destino = lote_para_entrada(session, horta_id, codigo, primeiro.produto, primeiro.unidade,
                                datos.data, primeiro.cultivo_siex_codigo,
                                primeiro.produto_animal,
                                protexido=all(lt.protexido for lt in lotes))
    mestura = Mestura(horta_id=horta_id, data=datos.data, lote_id=destino.id,
                      persoa_id=datos.persoa_id, horas=datos.horas, maquina_id=datos.maquina_id,
                      notas=datos.notas or None, creado_por=actor.id,
                      orixes=[MesturaOrixe(lote_id=o.lote_id, cantidade=o.cantidade,
                                           clase=o.clase or None) for o in datos.orixes])
    session.add(mestura)
    session.commit()
    return mestura


def listar_mesturas(session: Session, actor: Usuario, horta_id: int) -> list[Mestura]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(Mestura).filter_by(horta_id=horta_id, baixa=False)
                .order_by(Mestura.data.desc(), Mestura.id.desc()))


def dar_de_baixa_mestura(session: Session, actor: Usuario, mestura: Mestura) -> None:
    """Só se do lote novo aínda non saíu nada."""
    from horta.services.lotes import saido

    comprobar_rol_horta(session, mestura.horta_id, actor, _ROLES_ESCRITURA)
    if saido(session, _lote(session, mestura.lote_id)) > 1e-9:
        raise OperacionNonPermitidaError("Do lote da mestura xa saíu produto")
    mestura.baixa = True
    session.commit()


def orixes_do_lote(session: Session, lote_id: int) -> list[tuple[Lote, float, str | None]]:
    """De que lotes vén un lote feito por mestura (trazabilidade)."""
    return [(lote, o.cantidade, o.clase)
            for o in session.query(MesturaOrixe)
            .join(Mestura, Mestura.id == MesturaOrixe.mestura_id)
            .filter(Mestura.lote_id == lote_id, Mestura.baixa.is_(False))
            if (lote := session.get(Lote, o.lote_id)) is not None]
