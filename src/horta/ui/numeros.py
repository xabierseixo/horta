from __future__ import annotations

from datetime import date, time

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


def formatar_decimal(valor: float | int | None) -> str:
    """Mostra un número con coma decimal («9,8», «10»). Baleiro se é None."""
    if valor is None:
        return ""
    return f"{valor:g}".replace(".", ",")


def euros(valor: float) -> str:
    """Mostra un importe en euros con dous decimais e coma («85,40 €», «1 200,00 €»)."""
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def parsear_data(texto: str | None) -> date | None:
    """AAAA-MM-DD → date. Baleiro → None. Formato incorrecto → mensaxe clara."""
    if not texto or not texto.strip():
        return None
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        raise OperacionNonPermitidaError("Data non válida: usa AAAA-MM-DD") from None


def parsear_hora(texto: str | None) -> time | None:
    """HH:MM → time. Baleiro → None."""
    if not texto or not texto.strip():
        return None
    try:
        return time.fromisoformat(texto.strip())
    except ValueError:
        raise OperacionNonPermitidaError("Hora non válida: usa HH:MM") from None
