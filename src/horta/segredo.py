"""Segredo para asinar a cookie de sesión (S3).

Se falta HORTA_STORAGE_SECRET, a app non arranca cun segredo coñecido: crea un
ao chou a primeira vez e gárdao só para este usuario do sistema.
"""

from __future__ import annotations

import os
import secrets
from pathlib import Path

FICHEIRO_SEGREDO = Path.home() / ".local" / "share" / "horta" / "segredo-sesion"


def segredo_sesion(ficheiro: Path = FICHEIRO_SEGREDO) -> str:
    if valor := os.environ.get("HORTA_STORAGE_SECRET"):
        return valor
    if ficheiro.is_file():
        return ficheiro.read_text().strip()
    ficheiro.parent.mkdir(parents=True, exist_ok=True)
    valor = secrets.token_urlsafe(32)
    descritor = os.open(ficheiro, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descritor, "w") as f:
        f.write(valor)
    return valor
