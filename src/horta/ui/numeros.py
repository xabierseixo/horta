from __future__ import annotations

from datetime import date, time

from horta.idiomas import _
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
        raise OperacionNonPermitidaError(
            _("«{texto}» non é un número").format(texto=texto)
        ) from None


def formatar_decimal(valor: float | int | None) -> str:
    """Mostra un número con coma decimal («9,8», «10»). Baleiro se é None."""
    if valor is None:
        return ""
    return f"{valor:g}".replace(".", ",")


def formatar_enteiro(valor: float | int) -> str:
    """Mostra un enteiro con espazo nos miles («10 000»)."""
    return f"{valor:,.0f}".replace(",", " ")


def euros(valor: float) -> str:
    """Mostra un importe en euros con dous decimais e coma («85,40 €», «1 200,00 €»)."""
    return f"{valor:,.2f} €".replace(",", " ").replace(".", ",")


def parsear_data(texto: str | None) -> date | None:
    """DD/MM/AAAA (ou AAAA-MM-DD) → date. Baleiro → None. Formato incorrecto → mensaxe clara."""
    if not texto or not texto.strip():
        return None
    texto = texto.strip()
    try:
        if "/" in texto:
            dia, mes, ano = texto.split("/")
            return date(int(ano), int(mes), int(dia))
        return date.fromisoformat(texto)
    except ValueError:
        raise OperacionNonPermitidaError(_("Data non válida: usa DD/MM/AAAA")) from None


def texto_data(valor: date | str | None) -> str:
    """date ou AAAA-MM-DD → DD/MM/AAAA, como se escribe nos campos de data."""
    if not valor:
        return ""
    if isinstance(valor, str):
        try:
            return f"{date.fromisoformat(valor):%d/%m/%Y}"
        except ValueError:
            return valor
    return f"{valor:%d/%m/%Y}"


def parsear_hora(texto: str | None) -> time | None:
    """HH:MM → time. Baleiro → None."""
    if not texto or not texto.strip():
        return None
    try:
        return time.fromisoformat(texto.strip())
    except ValueError:
        raise OperacionNonPermitidaError(_("Hora non válida: usa HH:MM")) from None
