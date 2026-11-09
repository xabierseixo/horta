"""O que falta en cada paso do tratamento, todo xunto e antes de seguir (Y3), e a conta
da dose cando a etiqueta a dá en % do caldo (Y4). Sen NiceGUI, para probalo só."""

from __future__ import annotations

from typing import Any

from horta.idiomas import _
from horta.services.tratamentos_fito import UNIDADES_DOSE, UNIDADES_TOTAL
from horta.ui.numeros import parsear_data, parsear_decimal

REXISTRADO = "1"  # tipo de produto: fitosanitario rexistrado


def faltan_que_e_onde(data_inicio: str | None, data_fin: str | None,
                      cultivos: list[dict[str, Any]]) -> list[str]:
    faltan = []
    if parsear_data(data_inicio) is None or parsear_data(data_fin) is None:
        faltan.append(_("as datas de inicio e fin"))
    if not any(f["cultivo_id"] for f in cultivos):
        faltan.append(_("polo menos un cultivo tratado"))
    return faltan


def faltan_por_que(problemas: list[dict[str, Any]], xustificacions: list[str] | None
                   ) -> list[str]:
    faltan = []
    if not any(f["codigo"] for f in problemas):
        faltan.append(_("polo menos un problema (praga, enfermidade, mala herba...)"))
    if not xustificacions:
        faltan.append(_("polo menos unha xustificación"))
    return faltan


def faltan_con_que(produtos: list[dict[str, Any]], medidas: list[dict[str, Any]]
                   ) -> list[str]:
    usados = [f for f in produtos if f["nome"] or f["num"] or f["materia"]]
    if not usados and not any(f["tipo"] for f in medidas):
        return [_("polo menos un produto ou unha medida non química")]
    faltan = []
    for f in usados:
        nome = f["nome"] or f["num"] or f["materia"]
        dose = parsear_decimal(f["dose"])
        if dose is None or dose <= 0:
            faltan.append(_("a dose de {nome}").format(nome=nome))
        if not f["unidade"]:
            faltan.append(_("a unidade de {nome}").format(nome=nome))
        elif f["total"] and f["unidade"] not in UNIDADES_TOTAL:
            faltan.append(_("a cantidade total de {nome} en kg ou L").format(nome=nome))
        elif not f["total"] and f["unidade"] not in UNIDADES_DOSE:
            faltan.append(
                _("a dose de {nome} en kg/ha ou L/ha (ou marca que é o total)").format(nome=nome)
            )
        if f["tipo_produto"] == REXISTRADO and not f["num"]:
            faltan.append(_("o nº de rexistro de {nome}").format(nome=nome))
    return faltan


def faltan_quen(aplicador: int | None) -> list[str]:
    return [] if aplicador else [_("quen aplicou o tratamento")]


def cantidade_dende_porcentaxe(porcentaxe: float, litros_caldo: float) -> float:
    """Produto que leva o caldo: «0,5 %» en 16 L de mochila son 0,08 L (ou kg)."""
    return round(porcentaxe / 100 * litros_caldo, 4)


def ordenar_problemas(opcions: dict[str, str], do_cultivo: set[str], escollido: str | None
                      ) -> dict[str, str]:
    """Primeiro os problemas con usos autorizados no cultivo; os nomes repetidos («Fungi»
    cinco veces) só unha vez, agás o que xa estaba escollido (Y5)."""
    vistos: set[str] = set()
    resultado: dict[str, str] = {}
    for codigo in [c for c in opcions if c in do_cultivo] + [c for c in opcions
                                                             if c not in do_cultivo]:
        nome = opcions[codigo]
        if nome in vistos and codigo != escollido:
            continue
        vistos.add(nome)
        resultado[codigo] = nome
    return resultado
