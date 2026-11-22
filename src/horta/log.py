from __future__ import annotations

from pathlib import Path

from loguru import logger

_xa_configurado = False


def configurar_rexistro() -> None:
    """Configura loguru para escribir en logs/horta.log. Idempotente."""
    global _xa_configurado
    if _xa_configurado:
        return
    Path("logs").mkdir(exist_ok=True)
    logger.add(
        "logs/horta.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        backtrace=True,
        diagnose=False,
    )
    _xa_configurado = True
