"""Números dentro dun texto, como se escriben en galego: coma decimal (Y10)."""

from __future__ import annotations


def num_texto(valor: float) -> str:
    """0.3 → «0,3»; 2.0 → «2»; como moito tres decimais."""
    return f"{valor:.3f}".rstrip("0").rstrip(".").replace(".", ",")
