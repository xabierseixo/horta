"""Escoller unha ou varias leiras nos formularios de labor, rega e abonado
."""

from __future__ import annotations

from horta.services.leiras import LeiraTraballo


def leiras_escollidas(cultivos: list[int] | None, superficie_ha: float | None
                      ) -> list[LeiraTraballo]:
    """As leiras do formulario. A superficie só se pode indicar cunha leira; con varias, cada
    unha leva a do seu cultivo."""
    cultivos = list(cultivos or [])
    return [LeiraTraballo(c, superficie_ha if len(cultivos) == 1 else None) for c in cultivos]
