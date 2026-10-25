"""Plan de abonado: o aplicado nos abonados fronte ás necesidades do plan (kg/ha)."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.usuario import Usuario
from horta.services.abonados import listar_abonados, nutrientes_do_abonado


@dataclass
class Balance:
    """kg/ha de N, P₂O₅ e K₂O aplicados no cultivo e as necesidades do seu plan."""

    aplicado: tuple[float, float, float]
    necesidade: tuple[float | None, float | None, float | None]
    sen_calcular: int  # abonados dos que non se sabe a achega (p.ex. líquido sen densidade)


def balance_do_cultivo(
    session: Session, actor: Usuario, horta_id: int, cultivo: Cultivo
) -> Balance:
    """Suma a achega de cada abonado ponderada pola parte do cultivo que abonou."""
    n = p = k = 0.0
    sen_calcular = 0
    for abonado in listar_abonados(session, actor, horta_id, cultivo_id=cultivo.id):
        npk = nutrientes_do_abonado(session, abonado)
        if npk is None:
            sen_calcular += abonado.fertilizante_id is not None
            continue
        parte = (abonado.superficie_ha / cultivo.superficie_ha
                 if cultivo.superficie_ha else 1.0)
        n, p, k = n + npk[0] * parte, p + npk[1] * parte, k + npk[2] * parte
    return Balance(
        aplicado=(round(n, 1), round(p, 1), round(k, 1)),
        necesidade=(cultivo.plan_necesidade_n, cultivo.plan_necesidade_p2o5,
                    cultivo.plan_necesidade_k2o),
        sen_calcular=sen_calcular,
    )
