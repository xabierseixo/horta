"""Servizo do panel de explotacións (paso 168).

Resumo de todas as explotacións ás que ten acceso un usuario, cos seus avisos e
o último traballo feito, pensado para técnicos asesores e cooperativas.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.usuario import Usuario
from horta.services.diario import listar_traballos
from horta.services.documentos import documentos_con_aviso
from horta.services.en_regra import requisitos_en_regra
from horta.services.envio_cue import avisos_cue
from horta.services.faltas_caderno import faltas_caderno
from horta.services.hortas import listar_hortas_usuario
from horta.services.tarefas import listar_tarefas_atrasadas


@dataclass
class ResumoExplotacion:
    horta_id: int
    nome: str
    rol: str
    uso_profesional: bool
    requisitos_pendentes: int
    documentos_aviso: int
    faltas_caderno: int
    tarefas_atrasadas: int
    avisos_cue: int
    ultimo_traballo: date | None

    @property
    def total_avisos(self) -> int:
        return (
            self.requisitos_pendentes
            + self.documentos_aviso
            + self.faltas_caderno
            + self.tarefas_atrasadas
            + self.avisos_cue
        )


def resumo_explotacions(
    session: Session, actor: Usuario, hoxe: date | None = None
) -> list[ResumoExplotacion]:
    """Resumo de cada explotación do usuario, ordenadas por máis avisos e por nome."""
    dia = hoxe or date.today()
    inicio_ano = date(dia.year, 1, 1)
    limite_traballos = dia - timedelta(days=365)
    resumos: list[ResumoExplotacion] = []

    for horta, rol in listar_hortas_usuario(session, actor):
        rol_valor = rol.value if isinstance(rol, RolHorta) else str(rol)

        if horta.uso_profesional:
            reqs = requisitos_en_regra(session, actor, horta, hoxe=dia)
            req_pendentes = sum(1 for r in reqs if not r.cumprido)
            faltas = faltas_caderno(session, actor, horta.id, desde=inicio_ano)
            faltas_cantos = sum(f.cantos for f in faltas)
        else:
            req_pendentes = 0
            faltas_cantos = 0

        docs_aviso = len(documentos_con_aviso(session, actor, horta.id, hoxe=dia))
        atrasadas = len(listar_tarefas_atrasadas(session, actor, horta.id))
        cue_avisos = len(avisos_cue(session, actor, horta.id, hoxe=dia))

        traballos = listar_traballos(
            session, actor, horta.id, desde=limite_traballos, ata=dia, hoxe=dia
        )
        datas_feitos = [
            t.data
            for t in traballos
            if t.feito and t.data is not None and limite_traballos <= t.data <= dia
        ]
        ultimo = max(datas_feitos) if datas_feitos else None

        resumos.append(
            ResumoExplotacion(
                horta_id=horta.id,
                nome=horta.nome,
                rol=rol_valor,
                uso_profesional=horta.uso_profesional,
                requisitos_pendentes=req_pendentes,
                documentos_aviso=docs_aviso,
                faltas_caderno=faltas_cantos,
                tarefas_atrasadas=atrasadas,
                avisos_cue=cue_avisos,
                ultimo_traballo=ultimo,
            )
        )

    resumos.sort(key=lambda r: (-r.total_avisos, r.nome))
    return resumos
