"""Ficha de trazabilidade dun lote e simulacro de retirada (a documentación
§6.4 e §6bis): de onde veu (colleitas, producións e lotes mesturados, ata a orixe), que se lle
fixo (tratamentos e abonados dos cultivos; medicamentos dos animais), que pasou dentro
(clasificacións) e a onde foi (saídas e mesturas). Só le: non apunta nada."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.abonado import Abonado, AbonadoCultivo, Fertilizante
from horta.models.animal import Animal
from horta.models.coidado_animal import CoidadoAnimal
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.lote import (
    Clasificacion,
    Lote,
    LoteSaida,
    Mestura,
    MesturaOrixe,
    Transformacion,
    TransformacionEntrada,
)
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.producion_animal import ProducionAnimal
from horta.models.produto import EntradaProduto, Produto
from horta.models.tratamento_fito import TratamentoCultivo, TratamentoFito, TratamentoProduto
from horta.models.usuario import Usuario
from horta.services.catalogos import describir
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import CANLES, TIPOS_SAIDA
from horta.services.textos_catalogo import texto_catalogo

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


def _catalogo(session: Session, catalogo: str, codigo: str) -> str:
    return texto_catalogo(catalogo, codigo, describir(session, catalogo, codigo))


def _ecoloxico(session: Session, cultivo: Cultivo | None) -> str:
    if (cultivo is None or not cultivo.certificacion_ecoloxica
            or cultivo.certificacion_ecoloxica == "1"):
        return ""
    texto = _catalogo(session, "certificacion_ecoloxica", cultivo.certificacion_ecoloxica)
    if "ecolóxic" in texto.lower():
        return f" · {texto}"
    return f" · ecolóxico ({texto.lower()})"


def _texto_abonado(session: Session, ab: Abonado) -> str:
    fe = session.get(Fertilizante, ab.fertilizante_id) if ab.fertilizante_id else None
    partes: list[str] = []
    if fe is not None:
        partes.append(fe.nome)
        if fe.material:
            material = _catalogo(session, "material_fertilizante", fe.material)
            if material.lower() != fe.nome.lower():
                partes.append(material)
    else:
        partes.append(_catalogo(session, "boas_practicas", "20"))
    if ab.tipo_fertilizacion:
        tipo = _catalogo(session, "tipo_fertilizacion", ab.tipo_fertilizacion)
        if tipo.lower() not in {p.lower() for p in partes}:
            partes.append(tipo)
    if getattr(ab, "ecoloxico", False) or getattr(fe, "ecoloxico", False):
        partes.append("ecolóxico")
    return f"Abonado: {' · '.join(partes)}"


def _orixe(session: Session, lote: Lote, traz: Trazabilidade, cultivos: set[int],
           animais: set[int], fondo: int) -> None:
    prefixo = "" if fondo == 0 else f"[{lote.codigo}] "
    vistos: set[int] = set()
    for co in session.query(Colleita).filter_by(lote_id=lote.id, baixa=False):
        cultivo = session.get(Cultivo, co.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        especie = cultivo.especie if cultivo else "?"
        leira = parcela.nome if parcela else "?"
        eco = _ecoloxico(session, cultivo)
        if (co.cultivo_id not in vistos and cultivo is not None
                and cultivo.data_inicio is not None):
            vistos.add(co.cultivo_id)
            inicio = "Plantación" if cultivo.tipo_inicio == "plantacion" else "Sementeira"
            traz.orixe.append(Linea(cultivo.data_inicio,
                                    f"{prefixo}{inicio} de {especie} na leira {leira}{eco}"))
        cultivos.add(co.cultivo_id)
        traz.orixe.append(Linea(
            co.data,
            f"{prefixo}Colleita de {especie} na leira {leira}: {co.cantidade:g} {co.unidade}"
            f"{eco if cultivo is None or cultivo.data_inicio is None else ''}",
        ))
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
    for tr in session.query(Transformacion).filter_by(lote_id=lote.id, baixa=False):
        for e in tr.entradas:
            orixe = session.get(Lote, e.lote_id)
            if orixe is None:
                continue
            traz.orixe.append(Linea(tr.data, f"{prefixo}Elaborado con {e.cantidade:g} "
                                    f"{orixe.unidade}{f' ({e.clase})' if e.clase else ''} "
                                    f"do lote {orixe.codigo}"))
            if fondo < _FONDO:
                _orixe(session, orixe, traz, cultivos, animais, fondo + 1)
        for i in tr.insumos:
            produto = session.get(Produto, i.produto_id)
            entrada = session.get(EntradaProduto, i.entrada_id) if i.entrada_id else None
            lote_provedor = (f" · lote do provedor {entrada.lote_provedor}"
                             if entrada and entrada.lote_provedor else "")
            traz.orixe.append(Linea(tr.data, f"{prefixo}Ingrediente: "
                                    f"{produto.nome if produto else '?'} {i.cantidade:g} "
                                    f"{produto.unidade if produto else ''}{lote_provedor}"))


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
            traz.fixose.append(Linea(ab.data_inicio, _texto_abonado(session, ab)))
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
    return _construir(session, lote, con_saidas=True)


def _construir(session: Session, lote: Lote, con_saidas: bool) -> Trazabilidade:
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
    for te in (session.query(TransformacionEntrada)
               .join(Transformacion, Transformacion.id == TransformacionEntrada.transformacion_id)
               .filter(TransformacionEntrada.lote_id == lote.id,
                       Transformacion.baixa.is_(False))):
        tr = session.get(Transformacion, te.transformacion_id)
        destino = session.get(Lote, tr.lote_id) if tr else None
        traz.saidas.append(Linea(tr.data if tr else None,
                                 f"Transformado: {te.cantidade:g} {lote.unidade} no lote "
                                 f"{destino.codigo if destino else '?'}"))
    for o in (session.query(MesturaOrixe).join(Mestura, Mestura.id == MesturaOrixe.mestura_id)
              .filter(MesturaOrixe.lote_id == lote.id, Mestura.baixa.is_(False))):
        mestura = session.get(Mestura, o.mestura_id)
        destino = session.get(Lote, mestura.lote_id) if mestura else None
        traz.saidas.append(Linea(mestura.data if mestura else None,
                                 f"Mesturado: {o.cantidade:g} {lote.unidade} no lote "
                                 f"{destino.codigo if destino else '?'}"))
    if not con_saidas:
        traz.saidas = []
    for lista in (traz.orixe, traz.fixose, traz.dentro, traz.saidas):
        lista.sort(key=lambda linea: linea.data or date.min)
    return traz


# --- Páxina pública do lote (xemelgo dixital, paso 17)

def publicar_lote(session: Session, actor: Usuario, lote: Lote) -> str:
    """O enderezo secreto da páxina pública do lote (créase a primeira vez)."""
    comprobar_rol_horta(session, lote.horta_id, actor, {RolHorta.ADMIN, RolHorta.EDITOR})
    if lote.token_publico is None:
        lote.token_publico = secrets.token_urlsafe(24)
        session.commit()
    return lote.token_publico


def retirar_publicacion(session: Session, actor: Usuario, lote: Lote) -> None:
    comprobar_rol_horta(session, lote.horta_id, actor, {RolHorta.ADMIN, RolHorta.EDITOR})
    lote.token_publico = None
    session.commit()


def trazabilidade_publica(session: Session, token: str) -> tuple[Trazabilidade, str] | None:
    """Para quen merca: de onde vén, que se lle fixo e dentro do lote; nunca a quen se
    vendeu. Devolve tamén o nome da explotación."""
    lote = session.query(Lote).filter_by(token_publico=token, baixa=False).one_or_none()
    if lote is None:
        return None
    horta = session.get(Horta, lote.horta_id)
    return _construir(session, lote, con_saidas=False), horta.nome if horta else ""
