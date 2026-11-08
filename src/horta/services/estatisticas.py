"""Estatísticas (paso 15): produción por produto e ano, clases e refugo, choiva e auga de rega
por mes, e ingresos e gastos por mes. Só len o que xa está apuntado."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date

from sqlalchemy.orm import Session

from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.lote import Clasificacion, Lote
from horta.models.parcela import Parcela
from horta.models.producion_animal import ProducionAnimal
from horta.models.rega import Rega
from horta.models.tempo import TempoDia
from horta.models.usuario import Usuario
from horta.services.cartos import periodo, resumo_periodo
from horta.services.hortas import comprobar_rol_horta
from horta.services.lotes import converter
from horta.services.producions_animais import PRODUTOS

_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
# Catálogo UNIDADES_MEDIDA da rega: 3 = m³, 4 = litros
_M3_DA_UNIDADE = {"3": 1.0, "4": 0.001}


def _engadir(taboa: dict[str, dict[int, float]], nome: str, ano: int, cantidade: float,
             unidade: str) -> None:
    """Súmase en kg se se pode converter; se non, na súa unidade (no nome)."""
    kg = converter(cantidade, unidade, "kg")
    clave, valor = (nome, kg) if kg is not None else (f"{nome} ({unidade})", cantidade)
    taboa[clave][ano] = round(taboa[clave].get(ano, 0) + valor, 3)


def producion_por_ano(session: Session, actor: Usuario, horta_id: int, ata: int,
                      anos: int = 5) -> dict[str, dict[int, float]]:
    """Produto → ano → cantidade (kg cando se pode), dos últimos anos ata «ata»."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    desde = date(ata - anos + 1, 1, 1)
    fin = date(ata, 12, 31)
    taboa: dict[str, dict[int, float]] = defaultdict(dict)
    for co, especie in (session.query(Colleita, Cultivo.especie)
                        .join(Cultivo, Cultivo.id == Colleita.cultivo_id)
                        .join(Parcela, Parcela.id == Cultivo.parcela_id)
                        .filter(Parcela.horta_id == horta_id, Colleita.baixa.is_(False),
                                Colleita.data >= desde, Colleita.data <= fin)):
        _engadir(taboa, especie, co.data.year, co.cantidade, co.unidade)
    for pr in session.query(ProducionAnimal).filter(
            ProducionAnimal.horta_id == horta_id, ProducionAnimal.baixa.is_(False),
            ProducionAnimal.data >= desde, ProducionAnimal.data <= fin):
        _engadir(taboa, PRODUTOS.get(pr.produto, pr.produto), pr.data.year,
                 pr.cantidade - (pr.retirada or 0), pr.unidade)
    return dict(taboa)


def clases_do_ano(session: Session, actor: Usuario, horta_id: int, ano: int
                  ) -> dict[str, dict[str, float]]:
    """Produto → clase (e «Refugo») → cantidade clasificada no ano, na unidade do lote."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    taboa: dict[str, dict[str, float]] = defaultdict(dict)
    for cl, lote in (session.query(Clasificacion, Lote)
                     .join(Lote, Lote.id == Clasificacion.lote_id)
                     .filter(Clasificacion.horta_id == horta_id, Clasificacion.baixa.is_(False),
                             Clasificacion.data >= date(ano, 1, 1),
                             Clasificacion.data <= date(ano, 12, 31))):
        produto = f"{lote.produto} ({lote.unidade})"
        for linea in cl.clases:
            taboa[produto][linea.clase] = taboa[produto].get(linea.clase, 0) + linea.cantidade
        if cl.refugo:
            taboa[produto]["Refugo"] = taboa[produto].get("Refugo", 0) + cl.refugo
    return dict(taboa)


@dataclass
class AugaMes:
    choiva: list[float | None] = field(default_factory=lambda: [None] * 12)  # l/m²
    rega: list[float] = field(default_factory=lambda: [0.0] * 12)  # m³


def auga_por_mes(session: Session, actor: Usuario, horta_id: int, ano: int) -> AugaMes:
    """Choiva gardada na estación da explotación (só os días xa consultados) e auga de rega."""
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    auga = AugaMes()
    horta = session.get(Horta, horta_id)
    if horta is not None and horta.estacion_meteo_id is not None:
        for t in session.query(TempoDia).filter(
                TempoDia.estacion_id == horta.estacion_meteo_id,
                TempoDia.data >= date(ano, 1, 1), TempoDia.data <= date(ano, 12, 31),
                TempoDia.choiva.is_not(None)):
            mes = t.data.month - 1
            auga.choiva[mes] = round((auga.choiva[mes] or 0) + (t.choiva or 0), 1)
    for rega in session.query(Rega).filter(
            Rega.horta_id == horta_id, Rega.baixa.is_(False), Rega.cantidade.is_not(None),
            Rega.data_inicio >= date(ano, 1, 1), Rega.data_inicio <= date(ano, 12, 31)):
        mes = rega.data_inicio.month - 1
        auga.rega[mes] = round(auga.rega[mes] + (rega.cantidade or 0)
                               * _M3_DA_UNIDADE.get(rega.unidade, 0), 3)
    return auga


def cartos_por_mes(session: Session, actor: Usuario, horta_id: int, ano: int
                   ) -> tuple[list[float], list[float]]:
    """Ingresos e gastos de cada mes (o mesmo cálculo que en Contas)."""
    ingresos, gastos = [], []
    for mes in range(1, 13):
        resumo = resumo_periodo(session, actor, horta_id, periodo("mes", date(ano, mes, 1)))
        ingresos.append(resumo.total_ingresos)
        gastos.append(resumo.total_gastos)
    return ingresos, gastos
