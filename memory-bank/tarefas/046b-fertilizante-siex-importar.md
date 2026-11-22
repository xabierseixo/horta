# Tarefa 046b — Importar o catálogo oficial de abonos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 046. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Importador do ficheiro `DETALLE_MATERIAL_FERT.xlsx` do FEGA: altas, cambios e baixas (un produto que desaparece queda de baixa, non se borra), como `importar_cultivos`. `horta-catalogos importar` chámao se o ficheiro está no directorio. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md`.

## Ficheiros a tocar

- `src/horta/services/fertilizantes_importar.py` (**ficheiro novo**)
- `tests/services/test_fertilizantes_importar.py` (**ficheiro novo**)
- `src/horta/cli_catalogos.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/services/fertilizantes_importar.py`

Contido completo:
```python
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
```

### Paso 2 — crear o ficheiro `tests/services/test_fertilizantes_importar.py`

Contido completo:
```python
from datetime import date
from pathlib import Path

from openpyxl import Workbook

import horta.models  # noqa: F401
from horta.models.fertilizante import FertilizanteSiex
from horta.services.fertilizantes_importar import importar_fertilizantes

_CAB = ["Código SIEX", "Tipo material fertilizantes según lista SIEX", "C_FERTILIZANTE",
        "D_CLASIFICA_NIVEL1", "D_CLASIFICA_NIVEL2", "Nombre producto", "Fabricante",
        "D_FERTILIZANTE_2", "N_% TOTAL", "P2O5 % total", "K2O % total",
        "¿Inhibidor de la nitrificación? Si/No", "¿Inhibidor de la ureasa? Si/No",
        "Estado de agregación", "Densidad (g/cm3)"]


def _xlsx(ruta: Path, filas: list[list]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.append(_CAB)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)
    return ruta


def _fila(codigo: str, nome: str, n: str, liquido: str = "Sólido") -> list:
    return ["14", "Productos fertilizantes: abonos inorgánicos", codigo, "Simple",
            "NITROGENADO", nome, "GENÉRICO", f"{nome} de GENÉRICO", n, "0", "0", "NO", "SI",
            liquido, "1.41" if liquido == "Líquido" else "0"]


def test_importa_riqueza_e_estado(session, tmp_path):
    f = _xlsx(tmp_path / "DETALLE_MATERIAL_FERT.xlsx", [
        _fila("1", "ÁCIDO NÍTRICO (15-00-00)", "15", "Líquido"),
        _fila("2", "NITRATO AMÓNICO-NA (34,5-00-00)", "34.5"),
    ])
    informe = importar_fertilizantes(session, f)
    assert informe.altas == 2
    acido = session.get(FertilizanteSiex, 1)
    assert acido.material == "14"
    assert acido.n_pct == 15.0 and acido.liquido and acido.densidade == 1.41
    assert acido.inhibidor_ureasa and not acido.inhibidor_nitrificacion
    nitrato = session.get(FertilizanteSiex, 2)
    assert nitrato.n_pct == 34.5 and not nitrato.liquido and nitrato.densidade is None


def test_produto_que_desaparece_queda_de_baixa(session, tmp_path):
    importar_fertilizantes(session, _xlsx(tmp_path / "v1.xlsx", [
        _fila("1", "A (15-00-00)", "15"), _fila("2", "B (20-00-00)", "20")]))
    informe = importar_fertilizantes(session, _xlsx(tmp_path / "v2.xlsx", [
        _fila("1", "A (15-00-00)", "15")]), hoxe=date(2026, 11, 1))
    assert informe.baixas == 1
    assert session.get(FertilizanteSiex, 2).data_baixa == date(2026, 11, 1)


def test_mesmo_ficheiro_dúas_veces(session, tmp_path):
    f = _xlsx(tmp_path / "DETALLE_MATERIAL_FERT.xlsx", [_fila("1", "A (15-00-00)", "15")])
    importar_fertilizantes(session, f)
    assert importar_fertilizantes(session, f).xa_importado
```

### Paso 3 — `src/horta/cli_catalogos.py`: importar

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.fertilizantes_importar import importar_fertilizantes
```

### Paso 4 — `src/horta/cli_catalogos.py`: chamar ao importador

Antes:
```python
                print(f"variedade: {erro}")
```

Despois:
```python
                print(f"variedade: {erro}")
        fertilizantes = directorio / "DETALLE_MATERIAL_FERT.xlsx"
        if fertilizantes.exists():
            _imprimir(importar_fertilizantes(session, fertilizantes))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

`horta-catalogos importar` carga o catálogo oficial de abonos.
