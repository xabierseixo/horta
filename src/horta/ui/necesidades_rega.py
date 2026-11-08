"""Textos para amosar as necesidades de rega (método FAO-56 / SiAR)."""

from __future__ import annotations

from horta.services.necesidades_rega import NecesidadeRega
from horta.ui.numeros import formatar_decimal


def texto_necesidade(n: NecesidadeRega) -> str:
    """Devolve a explicación en texto das necesidades de rega calculadas para un cultivo."""
    if n.estado == "ok":
        falta = formatar_decimal(round(n.falta_mm, 1))
        etc = formatar_decimal(round(n.etc_mm, 1))
        choiva = formatar_decimal(round(n.choiva_efectiva_mm, 1))
        rega = formatar_decimal(round(n.rega_mm, 1))
        if n.falta_mm > 0:
            texto = (
                f"Faltan uns {falta} l/m² (gastou {etc}, choveu {choiva} útiles, regouse {rega})"
            )
        else:
            texto = (
                f"Non fai falta regar (gastou {etc} l/m², choveu {choiva} útiles, regouse {rega})"
            )
        if n.et0_estimada:
            texto += (
                " · aproximado: a estación non mide a evapotranspiración "
                "e calcúlase coa temperatura (FAO-56)"
            )
        elif n.aproximado:
            texto += " · cálculo aproximado"
        return texto

    if n.estado == "secano":
        return "Cultivo de secano"
    if n.estado == "sen_coeficiente":
        return "Non hai coeficiente oficial para este cultivo"
    if n.estado == "sen_estacion":
        return "Nin a parcela nin a explotación teñen estación de MeteoGalicia"
    if n.estado == "sen_data_inicio":
        return "Falta a data de sementeira ou plantación"
    if n.estado == "sen_datos":
        return "A estación non ten datos de temperatura nin evapotranspiración destes días"

    return ""
