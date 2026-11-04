"""Copias de seguridade: a base de datos e as fotos nun ZIP por día (S1).

As fai a propia app (ver horta.actualizacions), sen programar nada no sistema.
Gárdanse as últimas COPIAS_GARDADAS en HORTA_COPIAS_DIR; o admin descárgaas
para levalas fóra deste disco.
"""

from __future__ import annotations

import os
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine

from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.fotos import cartafol_fotos

COPIAS_GARDADAS = 30


@dataclass(frozen=True)
class Copia:
    nome: str
    data: datetime
    tamano: int


def cartafol_copias() -> Path:
    """HORTA_COPIAS_DIR ou, se non, ~/.local/share/horta/copias."""
    return Path(os.environ.get("HORTA_COPIAS_DIR")
                or Path.home() / ".local" / "share" / "horta" / "copias")


def facer_copia(engine: Engine, agora: datetime) -> Path:
    """Copia coherente da BD (VACUUM INTO, aínda que se estea a escribir) e das fotos."""
    destino = cartafol_copias()
    destino.mkdir(parents=True, exist_ok=True)
    ruta = destino / f"horta-{agora:%Y-%m-%d-%H%M}.zip"
    with tempfile.TemporaryDirectory() as temporal:
        bd = Path(temporal) / "horta.db"
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conexion:
            conexion.execute(text("VACUUM INTO :ruta"), {"ruta": str(bd)})
        parcial = ruta.with_suffix(".parcial")
        with zipfile.ZipFile(parcial, "w", zipfile.ZIP_DEFLATED) as zip_copia:
            zip_copia.write(bd, "horta.db")
            fotos = cartafol_fotos()
            if fotos.is_dir():
                for foto in sorted(fotos.rglob("*")):
                    if foto.is_file():
                        zip_copia.write(foto, f"fotos/{foto.relative_to(fotos).as_posix()}")
        parcial.replace(ruta)
    return ruta


def _copias_no_disco() -> list[Path]:
    return sorted(cartafol_copias().glob("horta-*.zip"))


def copia_diaria(engine: Engine, agora: datetime) -> Path | None:
    """Fai a copia do día se aínda non hai ningunha e borra as máis vellas."""
    if engine.url.get_backend_name() != "sqlite":
        return None
    if any(r.name.startswith(f"horta-{agora:%Y-%m-%d}") for r in _copias_no_disco()):
        return None
    ruta = facer_copia(engine, agora)
    for vella in _copias_no_disco()[:-COPIAS_GARDADAS]:
        vella.unlink()
    return ruta


def _esixir_admin(actor: Usuario) -> None:
    if actor.rol != RolGlobal.ADMIN:
        raise PermisoDenegadoError("Só un administrador pode ver as copias de seguridade")


def listar_copias(actor: Usuario) -> list[Copia]:
    _esixir_admin(actor)
    return [Copia(r.name, datetime.strptime(r.stem, "horta-%Y-%m-%d-%H%M"), r.stat().st_size)
            for r in reversed(_copias_no_disco())]


def ficheiro_da_copia(actor: Usuario, nome: str) -> Path | None:
    _esixir_admin(actor)
    return next((r for r in _copias_no_disco() if r.name == nome), None)
