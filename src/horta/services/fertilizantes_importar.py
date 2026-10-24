"""Importa o catálogo oficial de produtos fertilizantes (DETALLE_MATERIAL_FERT.xlsx do FEGA)."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from horta.models.fertilizante import FertilizanteSiex
from horta.services.catalogos_importar import (
    InformeImportacion,
    _codigo,
    _ler_xlsx,
    _nova_version,
    _texto,
    _xa_importado,
)


def _numero(valor: Any) -> float:
    texto = _texto(valor)
    return float(texto.replace(",", ".")) if texto else 0.0


def importar_fertilizantes(
    session: Session, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    hoxe = hoxe or date.today()
    if _xa_importado(session, "fertilizante", ruta):
        return InformeImportacion(catalogo="fertilizante", xa_importado=True)
    _, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo="fertilizante")
    version = _nova_version(session, "fertilizante", ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    existentes = {f.codigo: f for f in session.query(FertilizanteSiex)}
    vistos: set[int] = set()
    for fila in filas:
        codigo = int(_codigo(fila["C_FERTILIZANTE"]))
        vistos.add(codigo)
        densidade = _numero(fila.get("Densidad (g/cm3)"))
        datos = {
            "material": _codigo(fila["Código SIEX"]),
            "clase": _texto(fila.get("D_CLASIFICA_NIVEL1")),
            "subclase": _texto(fila.get("D_CLASIFICA_NIVEL2")),
            "nome": _texto(fila.get("D_FERTILIZANTE_2")) or "",
            "fabricante": _texto(fila.get("Fabricante")),
            "n_pct": _numero(fila.get("N_% TOTAL")),
            "p2o5_pct": _numero(fila.get("P2O5 % total")),
            "k2o_pct": _numero(fila.get("K2O % total")),
            "liquido": _texto(fila.get("Estado de agregación")) == "Líquido",
            "densidade": densidade or None,
            "inhibidor_nitrificacion":
                _texto(fila.get("¿Inhibidor de la nitrificación? Si/No")) == "SI",
            "inhibidor_ureasa": _texto(fila.get("¿Inhibidor de la ureasa? Si/No")) == "SI",
            "data_baixa": None,
        }
        actual = existentes.get(codigo)
        if actual is None:
            session.add(FertilizanteSiex(codigo=codigo, version_id=version.id, **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
    for codigo, fertilizante in existentes.items():
        if codigo not in vistos and fertilizante.data_baixa is None:
            fertilizante.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe
