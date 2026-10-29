"""Ficha de trazabilidade dun lote e simulacro de retirada (a documentación
§6.4 e §6bis): de onde veu (colleitas, producións e lotes mesturados, ata a orixe), que se lle
fixo (tratamentos e abonados dos cultivos; medicamentos dos animais), que pasou dentro
(clasificacións) e a onde foi (saídas e mesturas). Só le: non apunta nada."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, AbonadoCultivo
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.lote import Clasificacion, Lote, LoteSaida, Mestura, MesturaOrixe
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import Produto
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import CANLES, TIPOS_SAIDA

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Ata onde se segue unha mestura de mesturas
_FONDO = 5


@dataclass(frozen=True)
class Linea:
    data: date | None
    texto: str


@dataclass
class Trazabilidade:
    lote: Lote
    orixe: list[Linea] = field(default_factory=list)
    fixose: list[Linea] = field(default_factory=list)
    dentro: list[Linea] = field(default_factory=list)
    saidas: list[Linea] = field(default_factory=list)


def _nome(persoa: Persoa | None) -> str:
    return f"{persoa.nome} {persoa.apelidos or ''}".strip() if persoa else ""


def _orixe(session: Session, lote: Lote, traz: Trazabilidade, cultivos: set[int],
           animais: set[int], fondo: int) -> None:
    prefixo = "" if fondo == 0 else f"[{lote.codigo}] "
    for co in session.query(Colleita).filter_by(lote_id=lote.id, baixa=False):
        cultivo = session.get(Cultivo, co.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        cultivos.add(co.cultivo_id)
        especie = cultivo.especie if cultivo else "?"
        traz.orixe.append(Linea(co.data, f"{prefixo}Colleita de {especie}"
                                f" na leira {parcela.nome if parcela else '?'}: "
                                f"{co.cantidade:g} {co.unidade}"))
    for pr in session.query(ProducionAnimal).filter_by(lote_id=lote.id, baixa=False):
        animal = session.get(Animal, pr.animal_id)
        animais.add(pr.animal_id)
        grupo = animal.especie if animal else "?"
        traz.orixe.append(Linea(pr.data, f"{prefixo}Produción de {grupo}"
                                f": {pr.cantidade - (pr.retirada or 0):g} {pr.unidade}"))
    for me in session.query(Mestura).filter_by(lote_id=lote.id, baixa=False):
        for o in me.orixes:
            orixe = session.get(Lote, o.lote_id)
            if orixe is None:
                continue
            traz.orixe.append(Linea(me.data, f"{prefixo}Mestura: {o.cantidade:g} {orixe.unidade}"
                                    f"{f' ({o.clase})' if o.clase else ''} do lote "
                                    f"{orixe.codigo}"))
            if fondo < _FONDO:
                _orixe(session, orixe, traz, cultivos, animais, fondo + 1)


def _fixose(session: Session, traz: Trazabilidade, cultivos: set[int], animais: set[int]
            ) -> None:
    if cultivos:
        for tr in (session.query(TratamentoFito)
                   .join(TratamentoCultivo, TratamentoCultivo.tratamento_id == TratamentoFito.id)
                   .filter(TratamentoCultivo.cultivo_id.in_(cultivos),
                           TratamentoFito.baixa.is_(False)).distinct()):
            produtos = ", ".join(
                f"{p.nome_comercial or p.tipo_produto}"
                f"{f' (nº {p.num_rexistro})' if p.num_rexistro else ''}"
                for p in session.query(TratamentoProduto).filter_by(tratamento_id=tr.id))
            traz.fixose.append(Linea(tr.data_inicio, f"Tratamento: {produtos or 'sen produto'}"))
        for ab in (session.query(Abonado)
                   .join(AbonadoCultivo, AbonadoCultivo.abonado_id == Abonado.id)
                   .filter(AbonadoCultivo.cultivo_id.in_(cultivos), Abonado.baixa.is_(False))
                   .distinct()):
            traz.fixose.append(Linea(ab.data_inicio, "Abonado"))
    if animais:
        for co in session.query(CoidadoAnimal).filter(CoidadoAnimal.animal_id.in_(animais),
                                                      CoidadoAnimal.baixa.is_(False),
                                                      CoidadoAnimal.produto_id.is_not(None)):
            produto = session.get(Produto, co.produto_id)
            traz.fixose.append(Linea(co.data_inicio,
                                     f"Medicamento: {produto.nome if produto else '?'}"))


def trazabilidade(session: Session, actor: Usuario, lote_id: int) -> Trazabilidade:
    lote = session.get(Lote, lote_id)
    if lote is None:
        raise OperacionNonPermitidaError("Ese lote non existe")
    comprobar_rol_horta(session, lote.horta_id, actor, _ROLES_LECTURA)
    traz = Trazabilidade(lote)
    cultivos: set[int] = set()
    animais: set[int] = set()
    _orixe(session, lote, traz, cultivos, animais, 0)
    _fixose(session, traz, cultivos, animais)
    for cl in session.query(Clasificacion).filter_by(lote_id=lote.id, baixa=False):
        clases = ", ".join(f"{c.clase} {c.cantidade:g}" for c in cl.clases)
        traz.dentro.append(Linea(cl.data, f"Clasificación: {clases}"
                                 + (f", refugo {cl.refugo:g}" if cl.refugo else "")))
    for sa in session.query(LoteSaida).filter_by(lote_id=lote.id, baixa=False):
        quen = _nome(session.get(Persoa, sa.comprador_id)) if sa.comprador_id else ""
        onde = quen or sa.lugar or CANLES.get(sa.canle or "", "")
        traz.saidas.append(Linea(sa.data, f"{TIPOS_SAIDA[sa.tipo].split(' (')[0]}: "
                                 f"{sa.cantidade:g} {sa.unidade}"
                                 f"{f' ({sa.clase})' if sa.clase else ''}"
                                 f"{f' · {onde}' if onde else ''}"))
    for o in (session.query(MesturaOrixe).join(Mestura, Mestura.id == MesturaOrixe.mestura_id)
              .filter(MesturaOrixe.lote_id == lote.id, Mestura.baixa.is_(False))):
        mestura = session.get(Mestura, o.mestura_id)
        destino = session.get(Lote, mestura.lote_id) if mestura else None
        traz.saidas.append(Linea(mestura.data if mestura else None,
                                 f"Mesturado: {o.cantidade:g} {lote.unidade} no lote "
                                 f"{destino.codigo if destino else '?'}"))
    for lista in (traz.orixe, traz.fixose, traz.dentro, traz.saidas):
        lista.sort(key=lambda linea: linea.data or date.min)
    return traz
