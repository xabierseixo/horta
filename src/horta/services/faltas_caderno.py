"""Que lle falta ao apuntado para o caderno oficial (CUE). Só avisa: apuntar un traballo
nunca esixe os datos do caderno, que só é obrigatorio nas explotacións profesionais."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.foto import Foto
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados
from horta.services.labores import listar_labores
from horta.services.regas import listar_regas
from horta.services.tratamentos_fito import faltas_para_cue, listar_tratamentos_fito


@dataclass(frozen=True)
class Falta:
    traballo: str  # "Regas"
    dato: str  # "sistema de rega"
    cantos: int


def _contar(traballo: str, rexistros: list[Any],
            comprobacions: Iterable[tuple[str, Callable[[Any], bool]]]) -> list[Falta]:
    faltas = []
    for dato, falta in comprobacions:
        cantos = sum(1 for r in rexistros if falta(r))
        if cantos:
            faltas.append(Falta(traballo, dato, cantos))
    return faltas


def faltas_caderno(session: Session, actor: Usuario, horta_id: int,
                   desde: date | None = None, ata: date | None = None) -> list[Falta]:
    """Os datos que faltan, por tipo de traballo, nos rexistros do período."""
    def no_periodo(data: date) -> bool:
        return (desde is None or data >= desde) and (ata is None or data <= ata)

    regas = [r for r in listar_regas(session, actor, horta_id) if no_periodo(r.data_inicio)]
    abonados = [a for a in listar_abonados(session, actor, horta_id) if no_periodo(a.data_inicio)]
    labores = [lab for lab in listar_labores(session, actor, horta_id)
               if no_periodo(lab.data_inicio)]
    tratamentos = [t for t in listar_tratamentos_fito(session, actor, horta_id)
                   if no_periodo(t.data_inicio)]
    # Orde AAA/1072/2013 art. 4.a: quen aplica os lodos entrega o anexo III e gárdase 3 anos
    con_documento = {f.ref_id for f in session.query(Foto).filter_by(
        horta_id=horta_id, que="abonado", baixa=False)}
    return [
        *_contar("Tratamentos", tratamentos, [
            ("datos do CUE (ver a táboa de tratamentos)", lambda t: bool(faltas_para_cue(t)))]),
        *_contar("Abonados", abonados, [
            ("superficie", lambda a: any(not le.superficie_ha for le in a.leiras)),
            ("tipo de fertilización", lambda a: not a.tipo_fertilizacion),
            ("método de aplicación", lambda a: not a.metodo),
            ("boas prácticas", lambda a: not a.boas_practicas),
            ("dose", lambda a: a.fertilizante_id is not None and a.dose is None),
            ("copia do documento de aplicación dos lodos (anexo III da Orde AAA/1072/2013): "
             "gárdaa como foto no abonado",
             lambda a: a.aplicacion_lodos and a.id not in con_documento)]),
        *_contar("Regas", regas, [
            ("superficie", lambda r: any(not le.superficie_ha for le in r.leiras)),
            ("sistema de rega", lambda r: not r.sistema_rega),
            ("cantidade de auga", lambda r: r.cantidade is None)]),
        *_contar("Labores", labores, [
            ("superficie", lambda lab: any(not le.superficie_ha for le in lab.leiras))]),
    ]
