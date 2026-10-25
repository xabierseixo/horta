"""Colleitas dos cultivos (CUE bloque Cosecha), cada unha co seu lote. Baixa lóxica."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
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
    albaran_factura: str | None = None
    cliente_nome: str | None = None
    cliente_nif: str | None = None
    cliente_enderezo: str | None = None
    cliente_reaga: str | None = None
    obten_sementes: bool = False
    obten_plantas: bool = False
    sen_colleita_ambiental: bool = False
    restos_no_solo: bool = False
    maquina_id: int | None = None
    num_repeticions: int | None = None
    duracion_h_ha: float | None = None


def _cultivo_e_horta(session: Session, cultivo_id: int) -> tuple[Cultivo, int]:
    cultivo = session.get(Cultivo, cultivo_id)
    if cultivo is None:
        raise OperacionNonPermitidaError("Ese cultivo non existe")
    horta_id = session.query(Parcela.horta_id).filter_by(id=cultivo.parcela_id).scalar()
    return cultivo, horta_id


def _lotes_da_horta(session: Session, horta_id: int, excepto_id: int | None = None) -> set[str]:
    consulta = (
        session.query(Colleita.lote)
        .join(Cultivo, Colleita.cultivo_id == Cultivo.id)
        .join(Parcela, Cultivo.parcela_id == Parcela.id)
        .filter(Parcela.horta_id == horta_id)
    )
    if excepto_id is not None:
        consulta = consulta.filter(Colleita.id != excepto_id)
    return {lote for (lote,) in consulta}


def _validar(
    session: Session,
    datos: DatosColleita,
    cultivo: Cultivo,
    horta_id: int,
    hoxe: date,
    excepto_id: int | None = None,
) -> None:
    if datos.cantidade is None or datos.cantidade <= 0:
        raise OperacionNonPermitidaError("A cantidade ten que ser maior que 0")
    if datos.unidade not in UNIDADES_COLLEITA:
        raise OperacionNonPermitidaError(f"Unidade non válida: {datos.unidade}")
    if datos.data > hoxe:
        raise OperacionNonPermitidaError("A data da colleita non pode ser futura")
    if cultivo.data_inicio is not None and datos.data < cultivo.data_inicio:
        raise OperacionNonPermitidaError("A colleita non pode ser anterior ao inicio do cultivo")
    if datos.superficie_ha is not None:
        if datos.superficie_ha <= 0:
            raise OperacionNonPermitidaError("A superficie ten que ser maior que 0")
        if cultivo.superficie_ha and datos.superficie_ha > cultivo.superficie_ha:
            raise OperacionNonPermitidaError("A superficie colleitada é maior ca do cultivo")
    lote = datos.lote.strip()
    if not lote:
        raise OperacionNonPermitidaError("O lote é obrigatorio")
    if lote in _lotes_da_horta(session, horta_id, excepto_id):
        raise OperacionNonPermitidaError(f"O lote {lote} xa existe nesta explotación")
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


def _copiar(colleita: Colleita, datos: DatosColleita) -> None:
    colleita.cultivo_id = datos.cultivo_id
    colleita.data = datos.data
    colleita.cantidade = datos.cantidade
    colleita.unidade = datos.unidade
    colleita.lote = datos.lote.strip()
    colleita.superficie_ha = datos.superficie_ha
    colleita.data_fin = datos.data_fin or datos.data
    colleita.albaran_factura = datos.albaran_factura or None
    colleita.obten_sementes = datos.obten_sementes
    colleita.obten_plantas = datos.obten_plantas
    colleita.sen_colleita_ambiental = datos.sen_colleita_ambiental
    colleita.restos_no_solo = datos.restos_no_solo
    colleita.maquina_id = datos.maquina_id
    colleita.num_repeticions = datos.num_repeticions
    colleita.duracion_h_ha = datos.duracion_h_ha
    colleita.destino_colleita = datos.destino_colleita or None
    colleita.destino_restos = datos.destino_restos or None
    colleita.notas = datos.notas or None
    colleita.cliente_nome = datos.cliente_nome or None
    colleita.cliente_nif = datos.cliente_nif or None
    colleita.cliente_enderezo = datos.cliente_enderezo or None
    colleita.cliente_reaga = datos.cliente_reaga or None


def crear_colleita(
    session: Session, actor: Usuario, datos: DatosColleita, hoxe: date | None = None
) -> Colleita:
    cultivo, horta_id = _cultivo_e_horta(session, datos.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(session, datos, cultivo, horta_id, hoxe or date.today())
    if datos.superficie_ha is None:
        datos.superficie_ha = cultivo.superficie_ha
    colleita = Colleita(creado_por=actor.id)
    _copiar(colleita, datos)
    session.add(colleita)
    session.commit()
    return colleita


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
    _validar(session, datos, cultivo, horta_id, hoxe or date.today(), excepto_id=colleita.id)
    _copiar(colleita, datos)
    session.commit()
    return colleita


def dar_de_baixa_colleita(session: Session, actor: Usuario, colleita: Colleita) -> None:
    _, horta_id = _cultivo_e_horta(session, colleita.cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
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


def nome_para_lote(especie: str) -> str:
    """'Pemento de Padrón' -> 'PEMENTO': primeira palabra, sen acentos, ata 10 letras."""
    sen_acentos = unicodedata.normalize("NFKD", especie).encode("ascii", "ignore").decode()
    palabras = "".join(c if c.isalnum() else " " for c in sen_acentos).split()
    return palabras[0].upper()[:10] if palabras else "CULTIVO"


def propor_lote(session: Session, actor: Usuario, cultivo_id: int, data: date) -> str:
    """Primeiro lote libre do tipo AAAA-CULTIVO-NNN (p.ex. 2026-PATACA-001)."""
    cultivo, horta_id = _cultivo_e_horta(session, cultivo_id)
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    nome = nome_para_lote(cultivo.especie)
    existentes = _lotes_da_horta(session, horta_id)
    numero = 1
    while f"{data.year}-{nome}-{numero:03d}" in existentes:
        numero += 1
    return f"{data.year}-{nome}-{numero:03d}"


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
