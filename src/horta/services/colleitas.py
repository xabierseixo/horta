"""Colleitas dos cultivos (CUE bloque Cosecha). Cada colleita entra nun lote (services.lotes),
de onde sae despois a venda. Baixa lóxica."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import (
    codigo_por_agrupacion,
    comprobar_entrada,
    cultivo_protexido,
    ficha_para,
    lote_para_entrada,
)
from horta.services.persoas import comprobar_quen

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

UNIDADES_COLLEITA = ("kg", "t", "unidades", "ducias", "mazos", "litros")
_A_KG = {"kg": 1.0, "t": 1000.0}
# Anexo V CUE campo 516: finalidade só con destino "Vinificación" (22) ou "Outro procesamento"
_DESTINOS_CON_FINALIDADE = ("22", "23")


@dataclass
class DatosColleita:
    cultivo_id: int
    data: date
    cantidade: float
    unidade: str
    lote: str
    superficie_ha: float | None = None
    destino_colleita: str | None = None
    destino_restos: str | None = None
    notas: str | None = None
    data_fin: date | None = None
    obten_sementes: bool = False
    obten_plantas: bool = False
    sen_colleita_ambiental: bool = False
    restos_no_solo: bool = False
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h_ha: float | None = None
    persoa_id: int | None = None
    horas: float | None = None


def _cultivo_e_horta(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    return cultivo, horta_id


def _validar(
    session: Session,
    datos: DatosColleita,
    cultivo: Cultivo,
    horta_id: int,
    hoxe: date,
) -> None:
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if datos.unidade not in UNIDADES_COLLEITA:
        raise OperacionNonPermitidaError(f"Unidade non válida: {datos.unidade}")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data da colleita non pode ser futura")
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    if cultivo.data_inicio is not None and datos.data < cultivo.data_inicio:
        raise OperacionNonPermitidaError("A colleita non pode ser anterior ao inicio do cultivo")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie colleitada é maior ca do cultivo")
    if datos.data_fin is not None and datos.data_fin < datos.data:
        raise OperacionNonPermitidaError("A data de fin non pode ser anterior á de inicio")
    if datos.destino_colleita:
        if cultivo.destino not in _DESTINOS_CON_FINALIDADE:
            raise OperacionNonPermitidaError(
                "A finalidade só se indica se o cultivo vai a viño ou a procesado industrial"
            )
        validar_codigo(session, "destino_colleita", datos.destino_colleita, datos.data)
    if datos.destino_restos:
        validar_codigo(session, "destino_restos", datos.destino_restos, datos.data)


def _lote(session: Session, datos: DatosColleita, cultivo: Cultivo, horta_id: int) -> int:
    """O lote onde entra: o do código, se é o mesmo cultivo, ou un novo."""
    return lote_para_entrada(
        session, horta_id, datos.lote, cultivo.especie, datos.unidade, datos.data,
        cultivo_siex_codigo=cultivo.cultivo_siex_codigo,
        protexido=cultivo_protexido(cultivo)).id


def _copiar(colleita: Colleita, datos: DatosColleita) -> None:
    colleita.cultivo_id = datos.cultivo_id
    colleita.data = datos.data
    colleita.cantidade = datos.cantidade
    colleita.unidade = datos.unidade
    colleita.superficie_ha = datos.superficie_ha
    colleita.data_fin = datos.data_fin or datos.data
    colleita.obten_sementes = datos.obten_sementes
    colleita.obten_plantas = datos.obten_plantas
    colleita.sen_colleita_ambiental = datos.sen_colleita_ambiental
    colleita.restos_no_solo = datos.restos_no_solo
    colleita.maquina_id = datos.maquina_id
    colleita.num_repeticions = datos.num_repeticions
    colleita.duracion_h_ha = datos.duracion_h_ha
    colleita.persoa_id = datos.persoa_id
    colleita.horas = datos.horas
    colleita.destino_colleita = datos.destino_colleita or None
    colleita.destino_restos = datos.destino_restos or None
    colleita.notas = datos.notas or None


def _engadir(session: Session, actor: Usuario, datos: DatosColleita, hoxe: date) -> Colleita:
    """Valida e engade a colleita á sesión, sen gardar (commit)."""
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    if not datos.lote.strip():
        datos.lote = propor_lote(session, actor, datos.cultivo_id, datos.data)
    _validar(session, datos, cultivo, horta_id, hoxe)
    if datos.superficie_ha is None:
        datos.superficie_ha = cultivo.superficie_ha
    colleita = Colleita(creado_por=actor.id, lote_id=_lote(session, datos, cultivo, horta_id))
    _copiar(colleita, datos)
    session.add(colleita)
    session.flush()
    return colleita


def crear_colleita(
    session: Session, actor: Usuario, datos: DatosColleita, hoxe: date | None = None
) -> Colleita:
    colleita = _engadir(session, actor, datos, hoxe or date.today())
    session.commit()
    return colleita


def crear_colleitas(
    session: Session, actor: Usuario, datos: DatosColleita, cantidades: dict[int, float],
    hoxe: date | None = None,
) -> list[Colleita]:
    """A colleita de varias leiras dunha vez: unha colleita por leira (o CUE pídea por
    cultivo), coa cantidade de cada unha e todas no mesmo lote. As horas repártense pola
    cantidade. Ou se gardan todas ou ningunha."""
    if not cantidades:
        raise OperacionNonPermitidaError("Escolle polo menos unha leira")
    if any(c is None or c <= 0 for c in cantidades.values()):
        raise OperacionNonPermitidaError("Pon a cantidade colleitada en cada leira")
    cultivos = [session.get(Cultivo, c) for c in cantidades]
    if len({(c.cultivo_siex_codigo or c.especie.strip().lower()) for c in cultivos if c}) > 1:
        raise OperacionNonPermitidaError(
            "As leiras dunha mesma colleita van ao mesmo lote: teñen que ser do mesmo cultivo")
    total = sum(cantidades.values())
    colleitas = []
    try:
        for cultivo_id, cantidade in cantidades.items():
            parte = replace(
                datos, cultivo_id=cultivo_id, cantidade=cantidade, superficie_ha=None,
                horas=round(datos.horas * cantidade / total, 2) if datos.horas else None)
            colleitas.append(_engadir(session, actor, parte, hoxe or date.today()))
            # As seguintes van ao mesmo lote
            datos.lote = colleitas[0].lote
    except Exception:
        session.rollback()
        raise
    session.commit()
    return colleitas


def actualizar_colleita(
    session: Session,
    actor: Usuario,
    colleita: Colleita,
    datos: DatosColleita,
    hoxe: date | None = None,
) -> Colleita:
    if colleita.baixa:
        raise OperacionNonPermitidaError("Unha colleita dada de baixa non se pode modificar")
    _, horta_actual = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_actual, actor, _ROLES_ESCRITURA)
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    if horta_id != horta_actual:
        raise OperacionNonPermitidaError("O cultivo indicado non pertence a esta explotación")
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    lote_id = _lote(session, datos, cultivo, horta_id)
    # O lote de antes non pode quedar con menos do que xa saíu del
    comprobar_entrada(session, colleita.lote_id, colleita.cantidade, colleita.unidade,
                      datos.cantidade if lote_id == colleita.lote_id else 0, datos.unidade)
    colleita.lote_id = lote_id
    _copiar(colleita, datos)
    session.commit()
    return colleita


def dar_de_baixa_colleita(session: Session, actor: Usuario, colleita: Colleita) -> None:
    _, horta_id = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    comprobar_entrada(session, colleita.lote_id, colleita.cantidade, colleita.unidade, 0)
    colleita.baixa = True
    session.commit()


def listar_colleitas(
    session: Session,
    actor: Usuario,
    horta_id: int,
    cultivo_id: int | None = None,
    incluir_baixas: bool = False,
) -> list[Colleita]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = (
        session.query(Colleita)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if cultivo_id is not None:
        consulta = consulta.filter(Colleita.cultivo_id == cultivo_id)
    if not incluir_baixas:
        consulta = consulta.filter(Colleita.baixa.is_(False))
    return list(consulta.order_by(Colleita.data.desc(), Colleita.id.desc()))


def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
    """Primeiro lote libre do tipo AAAA-CULTIVO-NNN (p.ex. 2026-PATACA-001)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    ficha = ficha_para(session, horta_id, cultivo.especie, "kg", cultivo.cultivo_siex_codigo,
                       crear=False)
    return codigo_por_agrupacion(session, ficha, data)


def rendemento_kg_ha(session: Session, actor: Usuario, cultivo_id: int) -> float | None:
    """kg por hectárea; None se falta a superficie ou hai colleitas noutras unidades."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    colleitas = listar_colleitas(session, actor, horta_id, cultivo_id=cultivo_id)
    if not cultivo.superficie_ha or not colleitas:
        return None
    if any(c.unidade not in _A_KG for c in colleitas):
        return None
    total = sum(c.cantidade * _A_KG[c.unidade] for c in colleitas)
    return round(total / cultivo.superficie_ha, 1)
