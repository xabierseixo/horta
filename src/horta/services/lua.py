"""Fase da lúa, calculada (mes sinódico medio desde a lúa nova do 6/1/2000 ás 18:14 UTC).
Só informa: moita xente sementa segundo a lúa; a app non a usa para avisos."""

from __future__ import annotations

from datetime import date, datetime, timezone

_MES_SINODICO = 29.530588853
_LUA_NOVA = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
_FASES = ("Lúa nova", "Lúa crecente", "Cuarto crecente", "Lúa crecente", "Lúa chea",
          "Lúa minguante", "Cuarto minguante", "Lúa minguante")


def fase_lua(dia: date) -> str:
    mediodia = datetime(dia.year, dia.month, dia.day, 12, tzinfo=timezone.utc)
    idade = ((mediodia - _LUA_NOVA).total_seconds() / 86400) % _MES_SINODICO
    return _FASES[int((idade / _MES_SINODICO) * 8 + 0.5) % 8]
