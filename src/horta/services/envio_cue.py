"""Enviar o CUE á Xunta e levar o estado de cada actividade
.

- Só vai o novo e o que cambiou desde o último envío (a pegada do bloque é distinta).
- O que se deu de baixa despois de envialo vai co mesmo IdAjena e `Borrar: true`.
- As leiras alleas (AltaDGC) van unha soa vez: se se repiten, a Xunta dá erro.
- As actividades co que lles falta para o descritor quedan fóra, coa lista para completalas.
- O pechado na Xunta (xa pasou ao SIEX) non se volve enviar."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from horta.models.envio_cue import EnvioCue, RexistroCue
from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.cue import FaltaCue, Orixe, xerar_cue
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import titular_da_horta
from horta.services.xeaga import (
    CODIGOS_PECHADA,
    Token,
    Xeaga,
    actividades_procesadas,
)

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_ENVIADOS = ("enviado", "aceptado")


def _pegada(datos: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False)
                          .encode("utf-8")).hexdigest()


# Bloques da explotación que van unha soa vez (repetilos dá erro na Xunta); o seu id é o do
# cultivo do que saen
_UNHA_VEZ = ("AltaDGC", "CambioCultivoDGC")


def _id_ajena(datos: dict[str, Any]) -> int:
    return int(next(v for k, v in datos.items() if k.startswith("IdAjena")))


def _data(datos: dict[str, Any]) -> date | None:
    texto = datos.get("FechaInicio") or datos.get("FechaActuacion") or datos.get("Fecha")
    try:
        return datetime.strptime(texto, "%d/%m/%Y").date() if texto else None
    except ValueError:
        return None


@dataclass
class Saida:
    """Un bloque que vai no envío."""

    bloque: str
    id_ajena: int
    datos: dict[str, Any]
    orixe: Orixe


@dataclass
class Preparado:
    cuaderno: dict[str, Any]
    saidas: list[Saida] = field(default_factory=list)
    fora: list[FaltaCue] = field(default_factory=list)
    pechados: list[RexistroCue] = field(default_factory=list)


def preparar_envio(session: Session, actor: Usuario, horta_id: int, desde: date,
                   ata: date) -> Preparado:
    """O CUADERNO só co novo, o cambiado e o borrado do período."""
    cue = xerar_cue(session, actor, horta_id, desde, ata)
    faltas = cue.faltas()
    enviados = {(r.bloque, r.id_ajena): r for r in
                session.query(RexistroCue).filter_by(horta_id=horta_id)}
    preparado = Preparado({})

    def con_faltas(ruta: str) -> list[FaltaCue]:
        return [f for f in faltas if f.ruta == ruta or f.ruta.startswith(ruta + "/")]

    def vai(bloque: str, datos: dict[str, Any], ruta: str) -> bool:
        if (problemas := con_faltas(ruta)):
            preparado.fora.extend(problemas)
            return False
        rexistro = enviados.get((bloque, _id_ajena(datos)))
        if rexistro is not None and rexistro.estado == "pechado":
            preparado.pechados.append(rexistro)
            return False
        return rexistro is None or rexistro.borrado or rexistro.pegada != _pegada(datos) \
            or rexistro.estado == "erro"

    # Leiras alleas e cambios de cultivo: unha soa vez; os que teñen faltas deixan fóra o
    # que usa ese cultivo
    explotacion = dict(cue.datos.get("DatosExplotacion", {}))
    cultivos_mal: set[int] = set()
    for bloque in _UNHA_VEZ:
        quedan = []
        for n, datos in enumerate(explotacion.pop(bloque, []), 1):
            ruta = f"CUADERNO/DatosExplotacion/{bloque}[{n}]"
            orixe = cue.orixes[ruta]
            assert orixe.id is not None
            rexistro = enviados.get((bloque, orixe.id))
            if con_faltas(ruta) and not (rexistro and rexistro.estado in _ENVIADOS):
                preparado.fora.extend(con_faltas(ruta))
                cultivos_mal.add(orixe.id)
            elif rexistro is None or rexistro.estado == "erro":
                quedan.append(datos)
                preparado.saidas.append(Saida(bloque, orixe.id, datos, orixe))
        if quedan:
            explotacion[bloque] = quedan

    actividades: dict[str, list[dict[str, Any]]] = {}
    presentes = set()
    for bloque, lista in (cue.datos.get("ActividadesExplotacion") or {}).items():
        for n, datos in enumerate(lista, 1):
            presentes.add((bloque, _id_ajena(datos)))
            ruta = f"CUADERNO/ActividadesExplotacion/{bloque}[{n}]"
            if any(d.get("CodigoDGCAjena") in cultivos_mal for d in datos.get("DGCs", [])):
                continue
            if vai(bloque, datos, ruta):
                actividades.setdefault(bloque, []).append(datos)
                preparado.saidas.append(Saida(bloque, _id_ajena(datos), datos,
                                              cue.orixes[ruta]))

    # O enviado do período que xa non está (dado de baixa): bórrase na Xunta
    for (bloque, id_ajena), r in enviados.items():
        if (bloque in _UNHA_VEZ or (bloque, id_ajena) in presentes or r.borrado
                or r.estado not in _ENVIADOS or r.data is None or not desde <= r.data <= ata):
            continue
        datos = {**json.loads(r.datos), "Borrar": True}
        actividades.setdefault(bloque, []).append(datos)
        preparado.saidas.append(Saida(bloque, id_ajena, datos,
                                      Orixe(r.orixe_tipo, r.orixe_id, "Dado de baixa na app")))

    cabeceira = {k: v for k, v in cue.datos.items()
                 if k not in ("DatosExplotacion", "ActividadesExplotacion")}
    preparado.cuaderno = {**cabeceira, "DatosExplotacion": explotacion,
                          "ActividadesExplotacion": actividades}
    return preparado


def enviar(session: Session, actor: Usuario, horta_id: int, desde: date, ata: date,
           xeaga: Xeaga, token: Token) -> EnvioCue | None:
    """Envía o pendente do período. None se non hai nada que enviar."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    titular = titular_da_horta(session, horta_id)
    if not token.valido():
        raise OperacionNonPermitidaError("A conexión coa Xunta caducou: volve conectar")
    if titular is None or not titular.nif or token.nif != titular.nif:
        raise OperacionNonPermitidaError(
            "Quen se identificou na Xunta non é o titular desta explotación")
    preparado = preparar_envio(session, actor, horta_id, desde, ata)
    if not preparado.saidas:
        return None
    peticion = xeaga.crear(token, preparado.cuaderno)
    envio = EnvioCue(horta_id=horta_id, usuario_id=actor.id, desde=desde, ata=ata,
                     actividades=len(preparado.saidas), peticion=peticion)
    session.add(envio)
    session.flush()
    for saida in preparado.saidas:
        rexistro = session.query(RexistroCue).filter_by(
            horta_id=horta_id, bloque=saida.bloque, id_ajena=saida.id_ajena).one_or_none()
        if rexistro is None:
            rexistro = RexistroCue(horta_id=horta_id, bloque=saida.bloque,
                                   id_ajena=saida.id_ajena)
            session.add(rexistro)
        borrar = bool(saida.datos.get("Borrar"))
        datos = {k: v for k, v in saida.datos.items() if k != "Borrar"}
        rexistro.orixe_tipo, rexistro.orixe_id = saida.orixe.tipo, saida.orixe.id
        rexistro.data = _data(datos) or rexistro.data
        rexistro.pegada, rexistro.datos = _pegada(datos), json.dumps(datos, ensure_ascii=False)
        rexistro.borrado, rexistro.estado, rexistro.mensaxe = borrar, "enviado", None
        rexistro.envio_id = envio.id
    session.commit()
    return envio


def comprobar(session: Session, actor: Usuario, envio: EnvioCue, xeaga: Xeaga,
              token: Token) -> EnvioCue:
    """Pregunta á Xunta como quedou o envío e anota o estado de cada actividade."""
    comprobar_rol_horta(session, envio.horta_id, actor, _ROLES_ESCRITURA)
    if envio.peticion is None:
        return envio
    resultado = xeaga.comprobar_estado(token, envio.peticion)
    envio.comprobado = datetime.now(timezone.utc)
    if resultado.pendente:
        session.commit()
        return envio
    envio.resultado = resultado.codigo or "FALLO"
    envio.mensaxes = "\n".join(m.texto for m in resultado.mensaxes) or None
    pechada = any(m.codigo in CODIGOS_PECHADA for m in resultado.mensaxes)
    procesadas = {(a.bloque, a.id_ajena): a for a in actividades_procesadas(resultado)}
    for r in session.query(RexistroCue).filter_by(envio_id=envio.id):
        actividade = procesadas.get((r.bloque, r.id_ajena))
        if actividade is not None and actividade.valida:
            r.estado, r.mensaxe, r.id_cuaderno = "aceptado", None, actividade.id_cuaderno
        elif r.bloque in _UNHA_VEZ and envio.resultado in ("OK", "PARCIAL"):
            r.estado = "aceptado"
        else:
            r.estado = "pechado" if pechada else "erro"
            r.mensaxe = (envio.mensaxes or "Rexeitado pola Xunta")[:500]
    session.commit()
    return envio


def estado_cue(session: Session, actor: Usuario, horta_id: int) -> dict[tuple[str, int], str]:
    """O peor estado no CUE de cada traballo (tipo, id): erro > pechado > enviado > aceptado."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    orde = {"erro": 3, "pechado": 2, "enviado": 1, "aceptado": 0}
    estados: dict[tuple[str, int], str] = {}
    for r in session.query(RexistroCue).filter_by(horta_id=horta_id, borrado=False):
        if r.orixe_id is None:
            continue
        chave = (r.orixe_tipo, r.orixe_id)
        if orde[r.estado] >= orde.get(estados.get(chave, "aceptado"), 0):
            estados[chave] = r.estado
    return estados


def envios(session: Session, actor: Usuario, horta_id: int) -> list[EnvioCue]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(session.query(EnvioCue).filter_by(horta_id=horta_id)
                .order_by(EnvioCue.enviado.desc()))


# Datas límite dos envíos do CUE comercial ao CUE da Xunta (DT do FEGA 3.11 §5.4)
DATAS_LIMITE = ((3, 31), (9, 30))
_DIAS_AVISO = 30


def proxima_data_limite(hoxe: date) -> date:
    for ano in (hoxe.year, hoxe.year + 1):
        for mes, dia in DATAS_LIMITE:
            if date(ano, mes, dia) >= hoxe:
                return date(ano, mes, dia)
    raise AssertionError("inalcanzable")


def avisos_cue(session: Session, actor: Usuario, horta_id: int,
               hoxe: date | None = None) -> list[str]:
    """Para Inicio, só se a explotación xa envía o CUE desde horta: erros da Xunta e o
    pendente cando se achega unha data límite."""
    hoxe = hoxe or date.today()
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    if session.query(EnvioCue).filter_by(horta_id=horta_id).first() is None:
        return []
    avisos = []
    erros = session.query(RexistroCue).filter_by(horta_id=horta_id, estado="erro",
                                                 borrado=False).count()
    if erros:
        avisos.append(f"{erros} rexistros con erro no CUE da Xunta: revísaos en Informes.")
    limite = proxima_data_limite(hoxe)
    if (limite - hoxe).days <= _DIAS_AVISO:
        desde = date(limite.year - (1 if limite.month == 3 else 0), 1, 1)
        if preparar_envio(session, actor, horta_id, desde, hoxe).saidas:
            avisos.append(f"Antes do {limite:%d/%m/%Y} hai que enviar ao CUE da Xunta o que "
                          "falta (Informes → Caderno dixital).")
    return avisos
