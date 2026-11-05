"""O que falta en cada paso do tratamento, todo xunto e antes de seguir (Y3), e a conta
da dose cando a etiqueta a dá en % do caldo (Y4). Sen NiceGUI, para probalo só."""

from __future__ import annotations

from typing import Any

from horta.services.tratamentos_fito import UNIDADES_DOSE, UNIDADES_TOTAL
from horta.ui.numeros import parsear_data, parsear_decimal

REXISTRADO = "1"  # tipo de produto: fitosanitario rexistrado


def faltan_que_e_onde(data_inicio: str | None, data_fin: str | None,
                      cultivos: list[dict[str, Any]]) -> list[str]:
    faltan = []
    if parsear_data(data_inicio) is None or parsear_data(data_fin) is None:
        faltan.append("as datas de inicio e fin")
    if not any(f["cultivo_id"] for f in cultivos):
        faltan.append("polo menos un cultivo tratado")
    return faltan


def faltan_por_que(problemas: list[dict[str, Any]], xustificacions: list[str] | None
                   ) -> list[str]:
    faltan = []
    if not any(f["codigo"] for f in problemas):
        faltan.append("polo menos un problema (praga, enfermidade, mala herba...)")
    if not xustificacions:
        faltan.append("polo menos unha xustificación")
    return faltan


def faltan_con_que(produtos: list[dict[str, Any]], medidas: list[dict[str, Any]]
                   ) -> list[str]:
    usados = [f for f in produtos if f["nome"] or f["num"] or f["materia"]]
    if not usados and not any(f["tipo"] for f in medidas):
        return ["polo menos un produto ou unha medida non química"]
    faltan = []
    for f in usados:
        nome = f["nome"] or f["num"] or f["materia"]
        dose = parsear_decimal(f["dose"])
        if dose is None or dose <= 0:
            faltan.append(f"a dose de {nome}")
        if not f["unidade"]:
            faltan.append(f"a unidade de {nome}")
        elif f["total"] and f["unidade"] not in UNIDADES_TOTAL:
            faltan.append(f"a cantidade total de {nome} en kg ou L")
        elif not f["total"] and f["unidade"] not in UNIDADES_DOSE:
            faltan.append(f"a dose de {nome} en kg/ha ou L/ha (ou marca que é o total)")
        if f["tipo_produto"] == REXISTRADO and not f["num"]:
            faltan.append(f"o nº de rexistro de {nome}")
    return faltan


def faltan_quen(aplicador: int | None) -> list[str]:
    return [] if aplicador else ["quen aplicou o tratamento"]


def cantidade_dende_porcentaxe(porcentaxe: float, litros_caldo: float) -> float:
    """Produto que leva o caldo: «0,5 %» en 16 L de mochila son 0,08 L (ou kg)."""
    return round(porcentaxe / 100 * litros_caldo, 4)
