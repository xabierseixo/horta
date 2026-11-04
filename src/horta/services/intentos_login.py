"""Límite de intentos de acceso (S2): despois de varios contrasinais mal, facer esperar.

Gárdase en memoria: ao reiniciar a app bórrase, que abonda para frear as probas
automáticas de contrasinais dende internet.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from horta.services.auth import normalizar_email

INTENTOS_MAXIMOS = 5
ESPERA = timedelta(minutes=15)

_fallos: dict[str, list[datetime]] = {}


def minutos_de_espera(email: str, agora: datetime) -> int:
    """Minutos que faltan para poder tentalo de novo (0 se non hai que esperar)."""
    recentes = [d for d in _fallos.get(normalizar_email(email), []) if agora - d < ESPERA]
    if len(recentes) < INTENTOS_MAXIMOS:
        return 0
    falta = recentes[-INTENTOS_MAXIMOS] + ESPERA - agora
    return max(1, math.ceil(falta.total_seconds() / 60))


def apuntar_fallo(email: str, agora: datetime) -> None:
    for clave in [c for c, datas in _fallos.items() if agora - datas[-1] >= ESPERA]:
        del _fallos[clave]
    _fallos.setdefault(normalizar_email(email), []).append(agora)


def borrar_fallos(email: str) -> None:
    _fallos.pop(normalizar_email(email), None)
