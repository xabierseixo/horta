from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from horta.services.orixes import Orixe


def _convert_date_to_iso(value: Any) -> str:
    """Converte un valor de data a un string ISO 8601."""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value
    raise TypeError(f"Non se pode converter {type(value).__name__} a data ISO")


def _convert_date_from_iso(value: Any) -> date:
    """Converte un string ISO 8601 a un obxecto date."""
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    raise TypeError(f"Non se pode converter {type(value).__name__} a data")


@dataclass
class Cue:
    """O caderno dixital (CUE) para o período 2025–2026."""
    datos: dict[str, Any]
    orixes: dict[str, Orixe]
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

    def __post_init__(self) -> None:
        if self.fecha_inicio is not None:
            if isinstance(self.fecha_inicio, str):
                self.fecha_inicio = _convert_date_from_iso(self.fecha_inicio)
            elif isinstance(self.fecha_inicio, date):
                pass
        if self.fecha_fin is not None:
            if isinstance(self.fecha_fin, str):
                self.fecha_fin = _convert_date_from_iso(self.fecha_fin)
            elif isinstance(self.fecha_fin, date):
                pass

    @property
    def datos_explotacion(self) -> list[dict[str, Any]]:
        """Devolve a lista de actividades de explotación."""
        return self.datos.get("datos_explotacion", [])

    def a_dicionario(self) -> dict[str, Any]:
        """Converte o CUE a un dicionario para exportación."""
        return {
            "datos_explotacion": self.datos_explotacion,
            "fecha_inicio": _convert_date_to_iso(self.fecha_inicio),
            "fecha_fin": _convert_date_to_iso(self.fecha_fin),
        }

    def a_json(self, camiño: Path | str) -> None:
        """Garda o CUE como un ficheiro JSON."""
        camiño = Path(camiño)
        camiño.parent.mkdir(parents=True, exist_ok=True)
        with camiño.open("w", encoding="utf-8") as f:
            json.dump(self.a_dicionario(), f, indent=2, ensure_ascii=False)

    @classmethod
    def de_ficheiro(cls, camiño: Path | str) -> Cue:
        """Carga un CUE desde un ficheiro JSON."""
        camiño = Path(camiño)
        camiño.parent.mkdir(parents=True, exist_ok=True)
        with camiño.open("r", encoding="utf-8") as f:
            datos = json.load(f)
        return cls(datos=datos, orixes={})

    @classmethod
    def de_json(cls, json_str: str) -> Cue:
        """Carga un CUE desde un string JSON."""
        datos = json.loads(json_str)
        return cls(datos=datos, orixes={})


@dataclass
class ActividadExplotacion:
    """Representa unha actividade de explotación."""
    tipo: str
    datos: dict[str, Any] = field(default_factory=dict)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None

    def __post_init__(self) -> None:
        if self.fecha_inicio is not None:
            if isinstance(self.fecha_inicio, str):
                self.fecha_inicio = _convert_date_from_iso(self.fecha_inicio)
            elif isinstance(self.fecha_inicio, date):
                pass
        if self.fecha_fin is not None:
            if isinstance(self.fecha_fin, str):
                self.fecha_fin = _convert_date_from_iso(self.fecha_fin)
            elif isinstance(self.fecha_fin, date):
                pass



