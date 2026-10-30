"""O REA da Xunta (exportarREA) fronte ao que hai na app: emparellar cada cultivo coa súa
DGC (a parte dun recinto SIGPAC cun cultivo, DT do FEGA 3.11 §3.3) e mostrar as diferenzas.
Non se cambia nada sen que o usuario o acepte
."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import RolHorta
from horta.models.parcela import Parcela
from horta.models.usuario import Usuario
from horta.services.cultivos import listar_cultivos
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_SIGPAC = ("provincia", "municipio", "agregado", "zona", "poligono", "parcela", "recinto")


def _campo(datos: dict[str, Any], nome: str) -> Any:
    """O descritor usa camelCase e os exemplos antigos outras formas: sen ter en conta
    maiúsculas nin guións baixos."""
    clave = nome.lower().replace("_", "")
    return next((v for k, v in datos.items() if k.lower().replace("_", "") == clave), None)


def _int(valor: Any) -> int | None:
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return None


def _data(valor: Any) -> date | None:
    try:
        return datetime.strptime(str(valor), "%d/%m/%Y").date()
    except ValueError:
        return None


@dataclass
class CultivoRea:
    identificador: int | None
    cultivo: int | None
    variedade: int | None
    inicio: date | None
    fin: date | None


@dataclass
class DgcRea:
    codigo: int
    recinto: tuple[int | None, ...]
    superficie: float | None
    cultivos: list[CultivoRea] = field(default_factory=list)


def ler_dgcs(explotacions: list[dict[str, Any]]) -> list[DgcRea]:
    """As DGC vixentes (sen data de baixa) da resposta de exportarREA."""
    dgcs = []
    for explotacion in explotacions:
        for d in _campo(explotacion, "DGC") or []:
            codigo = _int(_campo(d, "codigoDGC"))
            if codigo is None or _campo(d, "fechaBaja"):
                continue
            xerais = _campo(d, "datosGeneralesDGC") or {}
            superficie = _campo(xerais, "superficieDGC")
            dgcs.append(DgcRea(
                codigo, tuple(_int(_campo(d, c)) for c in _SIGPAC),
                float(superficie) if superficie is not None else None,
                [CultivoRea(_int(_campo(c, "identificadorCultivo")), _int(_campo(c, "cultivo")),
                            _int(_campo(c, "variedad")), _data(_campo(c, "fechaInicio")),
                            _data(_campo(c, "fechaFin")))
                 for c in _campo(d, "cultivos") or [] if not _campo(c, "fechaBaja")]))
    return dgcs


def _recinto(parcela: Parcela | None) -> tuple[int | None, ...] | None:
    if parcela is None:
        return None
    ref = tuple(_int(v) for v in (
        parcela.sigpac_provincia, parcela.sigpac_concello, parcela.sigpac_agregado,
        parcela.sigpac_zona, parcela.sigpac_poligono, parcela.sigpac_parcela,
        parcela.sigpac_subparcela))
    return ref if None not in (ref[0], ref[1], ref[4], ref[5], ref[6]) else None


def _solapan(c: Cultivo, r: CultivoRea) -> bool:
    inicio, fin = c.data_inicio or date.min, c.data_fin or date.max
    return (r.inicio or date.min) <= fin and inicio <= (r.fin or date.max)


@dataclass
class Emparellado:
    cultivo_id: int
    texto: str
    codigo_dgc: int
    codigo_cultivo_rea: int | None  # None: no REA hai outro cultivo (cambio de cultivo)
    diferenzas: list[str]


@dataclass
class Comparacion:
    emparellados: list[Emparellado]
    so_na_xunta: list[DgcRea]
    so_na_app: list[str]


def comparar(session: Session, actor: Usuario, horta_id: int,
             dgcs: list[DgcRea]) -> Comparacion:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
    por_recinto: dict[tuple[int | None, ...], list[DgcRea]] = {}
    for d in dgcs:
        # Agregado e zona baleiros valen 0 no SIGPAC
        por_recinto.setdefault(tuple(v or 0 for v in d.recinto), []).append(d)
    emparellados, so_app, usadas = [], [], set()
    for c in listar_cultivos(session, actor, horta_id):
        parcela = parcelas.get(c.parcela_id)
        nome = f"{c.especie} en {parcela.nome if parcela else '?'}"
        recinto = _recinto(parcela)
        candidatas = por_recinto.get(tuple(v or 0 for v in recinto), []) if recinto else []
        if not candidatas:
            so_app.append(nome if recinto else f"{nome} (sen referencia SIGPAC)")
            continue
        # Na DGC onde o REA ten este mesmo cultivo nas mesmas datas; se non, a primeira
        escollida, cultivo_rea = candidatas[0], None
        for d in candidatas:
            cultivo_rea = next((r for r in d.cultivos if r.cultivo == c.cultivo_siex_codigo
                                and _solapan(c, r)), None)
            if cultivo_rea is not None:
                escollida = d
                break
        usadas.add(escollida.codigo)
        diferenzas = []
        if cultivo_rea is None:
            diferenzas.append("no REA este recinto ten outro cultivo: irá como cambio de "
                              "cultivo")
        if escollida.superficie is not None and c.superficie_ha is not None \
                and c.superficie_ha > escollida.superficie + 0.005:
            diferenzas.append(f"superficie {c.superficie_ha:g} ha na app e "
                              f"{escollida.superficie:g} ha na Xunta")
        emparellados.append(Emparellado(c.id, nome, escollida.codigo,
                                        cultivo_rea.identificador if cultivo_rea else None,
                                        diferenzas))
    return Comparacion(emparellados, [d for d in dgcs if d.codigo not in usadas], so_app)


def aceptar(session: Session, actor: Usuario, horta_id: int,
            emparellados: list[Emparellado]) -> int:
    """Garda nos cultivos a DGC e o cultivo do REA. Devolve cantos cambiaron."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    cultivos = {c.id: c for c in listar_cultivos(session, actor, horta_id)}
    cambiados = 0
    for e in emparellados:
        c = cultivos.get(e.cultivo_id)
        if c is None:
            raise OperacionNonPermitidaError("O cultivo non é desta explotación")
        if (c.codigo_dgc, c.codigo_cultivo_rea) != (e.codigo_dgc, e.codigo_cultivo_rea):
            c.codigo_dgc, c.codigo_cultivo_rea = e.codigo_dgc, e.codigo_cultivo_rea
            cambiados += 1
    session.commit()
    return cambiados
