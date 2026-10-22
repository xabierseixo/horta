from __future__ import annotations

from horta.services.errors import OperacionNonPermitidaError


def parsear_decimal(texto: str | float | int | None) -> float | None:
    """Acepta coma ou punto decimal ("1,5" → 1.5). Baleiro → None."""
    if texto is None:
        return None
    if isinstance(texto, (int, float)):
        return float(texto)
    limpo = texto.strip().replace(",", ".")
    if not limpo:
        return None
    try:
        return float(limpo)
    except ValueError:
        raise OperacionNonPermitidaError(f"«{texto}» non é un número") from None
