# Caderno de tratamentos conforme ao CUE — Fase 1: Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que horta rexistre os tratamentos fitosanitarios cos códigos e datos oficiais do CUE (catálogos FEGA, aplicadores con ROPO, equipos con ROMA/REGANIP, varios cultivos e produtos por tratamento), conservando os tratamentos existentes.

**Architecture:** Catálogos oficiais versionados en táboas propias (`catalogo_valor`, `cultivo_siex`, `variedade_siex`) cargados por un importador idempotente desde os XLSX do portal do FEGA; capa galega en táboas separadas. Novas entidades por horta (`persoa`, `maquina`) e novo agregado `tratamento_fito` con fillos (cultivos, problemas, xustificacións, produtos, medidas, aplicadores, asesor). Os servizos son a fronteira de validación e permisos, como no resto da app. A táboa antiga `tratamento` cópiase ao novo modelo e deixa de usarse na UI.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0, Alembic, NiceGUI, pytest, ruff, mypy, uv; nova dependencia `openpyxl` (xa prevista en CLAUDE.md para exportar Excel).

**Spec:** `docs/superpowers/specs/2026-10-22-caderno-tratamentos-fase1-design.md`

## Global Constraints

- Identificadores, mensaxes e textos da UI en galego.
- Os servizos reciben `session` e `actor` e comproban permisos con `comprobar_rol_horta` (escritura: admin/editor; lectura: admin/editor/lector).
- Erros de regra de negocio: `OperacionNonPermitidaError` (de `horta.services.errors`), con mensaxe clara en galego.
- Nunca se borra un código de catálogo: márcase `data_baixa`.
- Os tratamentos non se borran fisicamente (baixa lóxica, conservación legal 3 anos).
- Non se salta o reCAPTCHA do portal do FEGA: a descarga faise nun navegador normal.
- Liña máxima 100 caracteres (ruff), `uv run ruff check src tests`, `uv run mypy src`, `uv run pytest -q` en verde antes de cada commit (hook `.githooks/pre-commit`).
- Commits de Claude co rodapé `Axente: claude`; tarefas para smoth en `memory-bank/tarefas/NNN-*.md` con formato "Antes/Despois" e proba en seco previa.

## Review Focus

1. **Eliminar un cultivo ou parcela con tratamentos fitosanitarios rexistrados** → debe impedirse cunha mensaxe (conservación legal), non borrar en cascada. Test na Tarefa 7.
2. **Un código de catálogo dado de baixa despois de gardar un tratamento** → o tratamento segue sendo válido e amosa a descrición. Test na Tarefa 3 (`describir` inclúe baixas) e na Tarefa 7.
3. **Reimportar o mesmo ficheiro / ficheiro novo sen un código** → sen cambios / o código queda de baixa, non se borra. Tests na Tarefa 2.
4. **Carné ROPO que caduca exactamente o día do tratamento** → válido (caducidade ≥ data). Test na Tarefa 4 e na Tarefa 7.
5. **Horta de autoconsumo (sen uso profesional) con datos mínimos** → pódese gardar sen aplicador, xustificación nin asesor. Test na Tarefa 7.

---

## Mapa de ficheiros

| Ficheiro | Responsabilidade |
|---|---|
| `src/horta/models/catalogo.py` (novo) | CatalogoVersion, CatalogoValor, CultivoSiex, VariedadeSiex, NomeGalego, VariedadeLocal |
| `src/horta/services/catalogos_importar.py` (novo) | Ler XLSX e importar catálogos (idempotente, con versións) |
| `src/horta/services/catalogos.py` (novo) | Consultas: valores vixentes, validar código, describir, buscar cultivos |
| `src/horta/cli_catalogos.py` (novo) | Comando `horta-catalogos` |
| `src/horta/models/persoa.py`, `src/horta/services/persoas.py` (novos) | Aplicadores/asesores con ROPO |
| `src/horta/models/maquina.py`, `src/horta/services/maquinaria.py` (novos) | Equipos con ROMA/REGANIP |
| `src/horta/models/tratamento_fito.py` (novo) | Agregado tratamento fitosanitario CUE |
| `src/horta/services/tratamentos_fito.py` (novo) | Crear, actualizar, baixa, listar, validación, completitude CUE |
| `src/horta/services/cultivos.py`, `parcelas.py` (modificar) | Bloquear borrado se hai tratamentos CUE |
| `alembic/versions/xxxx_catalogos_persoas_maquinas.py`, `xxxx_tratamento_fito.py` (novos) | Esquema e copia de datos |
| `src/horta/ui/numeros.py` (novo) | `parsear_decimal` ("1,5" → 1.5) |
| `src/horta/ui/pages/persoas.py`, `maquinaria.py`, `tratamentos_fito.py` (novos) | Pestanas novas |
| `src/horta/ui/pages/horta_detalle.py` (modificar) | Só enlazar as pestanas novas e retirar a sección antiga de tratamentos |
| `src/horta/data/nomes_galegos.csv` (novo) | Nomes galegos e prioridade dos cultivos habituais en Galicia |
| `docs/referencia/siex/descarga-catalogos.md` (novo) | Procedemento de descarga mensual |

---

### Task 1: Modelos de catálogos e migración (Claude)

**Files:**
- Create: `src/horta/models/catalogo.py`
- Modify: `src/horta/models/__init__.py`
- Create: `alembic/versions/<auto>_catalogos.py` (autogenerado e revisado)
- Test: `tests/models/test_catalogo.py`

**Interfaces:**
- Produces: clases `CatalogoVersion`, `CatalogoValor`, `CultivoSiex`, `VariedadeSiex`, `NomeGalego`, `VariedadeLocal` (campos abaixo).

- [ ] **Step 1: Escribir o test que falla**

```python
# tests/models/test_catalogo.py
from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from horta.models.catalogo import (
    CatalogoValor,
    CatalogoVersion,
    CultivoSiex,
    NomeGalego,
    VariedadeLocal,
    VariedadeSiex,
)


def _version(session, catalogo="praga"):
    v = CatalogoVersion(catalogo=catalogo, nome_ficheiro="PLAGAS.xlsx", sha256="a" * 64, filas=1)
    session.add(v)
    session.commit()
    return v


def test_catalogo_valor_e_unico_por_catalogo_e_codigo(session):
    v = _version(session)
    session.add(CatalogoValor(catalogo="praga", codigo="1", descricion="Arthropoda", version_id=v.id))
    session.commit()
    session.add(CatalogoValor(catalogo="praga", codigo="1", descricion="Outra", version_id=v.id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_cultivo_variedade_e_capa_galega(session):
    v = _version(session, "cultivo")
    pataca = CultivoSiex(
        codigo=99, nome_oficial="PATATA", nome_latin="Solanum tuberosum",
        codigo_eppo="SOLTU", horticola=True, integrado=True, version_id=v.id,
    )
    session.add(pataca)
    session.add(VariedadeSiex(cultivo_codigo=99, codigo=0, nome_oficial="SIN VARIEDAD",
                              version_id=v.id))
    session.add(NomeGalego(catalogo="cultivo", codigo="99", nome_gl="Pataca", prioridade=10))
    session.add(VariedadeLocal(cultivo_codigo=99, nome="Fina de Carballo",
                               fonte="IXP Pataca de Galicia"))
    session.commit()
    assert pataca.data_baixa is None
    assert session.query(VariedadeLocal).one().cultivo_codigo == 99
    assert session.query(NomeGalego).one().nome_gl == "Pataca"


def test_data_baixa_opcional(session):
    v = _version(session)
    valor = CatalogoValor(catalogo="praga", codigo="2", descricion="X", version_id=v.id,
                          data_baixa=date(2026, 1, 1))
    session.add(valor)
    session.commit()
    assert valor.data_baixa == date(2026, 1, 1)
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/models/test_catalogo.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'horta.models.catalogo'`

- [ ] **Step 3: Implementar os modelos**

```python
# src/horta/models/catalogo.py
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class CatalogoVersion(Base):
    """Unha importación dun ficheiro oficial de catálogo (FEGA)."""

    __tablename__ = "catalogo_version"
    __table_args__ = (UniqueConstraint("catalogo", "sha256"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60))
    nome_ficheiro: Mapped[str] = mapped_column(String(255))
    sha256: Mapped[str] = mapped_column(String(64))
    filas: Mapped[int] = mapped_column(Integer)
    data_importacion: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class CatalogoValor(Base):
    """Valor dun catálogo xenérico do SIEX (pragas, unidades, xustificacións...)."""

    __tablename__ = "catalogo_valor"
    __table_args__ = (UniqueConstraint("catalogo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
    descricion: Mapped[str] = mapped_column(String(500))
    codigo_eppo: Mapped[str | None] = mapped_column(String(12), default=None)
    categoria: Mapped[str | None] = mapped_column(String(120), default=None)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class CultivoSiex(Base):
    __tablename__ = "cultivo_siex"

    codigo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    nome_oficial: Mapped[str] = mapped_column(String(200))
    nome_latin: Mapped[str | None] = mapped_column(String(200), default=None)
    codigo_eppo: Mapped[str | None] = mapped_column(String(12), default=None)
    codigo_upov: Mapped[str | None] = mapped_column(String(40), default=None)
    horticola: Mapped[bool] = mapped_column(Boolean, default=False)
    integrado: Mapped[bool] = mapped_column(Boolean, default=False)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class VariedadeSiex(Base):
    __tablename__ = "variedade_siex"
    __table_args__ = (UniqueConstraint("cultivo_codigo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_codigo: Mapped[int] = mapped_column(ForeignKey("cultivo_siex.codigo"), index=True)
    codigo: Mapped[int] = mapped_column(Integer)
    nome_oficial: Mapped[str] = mapped_column(String(300))
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class NomeGalego(Base):
    """Capa galega: nome en galego e prioridade de busca. Non a toca o importador."""

    __tablename__ = "nome_galego"
    __table_args__ = (UniqueConstraint("catalogo", "codigo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(60))
    codigo: Mapped[str] = mapped_column(String(20))
    nome_gl: Mapped[str] = mapped_column(String(200))
    prioridade: Mapped[int] = mapped_column(Integer, default=0)


class VariedadeLocal(Base):
    """Variedade tradicional galega que non está no catálogo do FEGA."""

    __tablename__ = "variedade_local"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_codigo: Mapped[int] = mapped_column(ForeignKey("cultivo_siex.codigo"))
    nome: Mapped[str] = mapped_column(String(200))
    fonte: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
```

Engadir a `src/horta/models/__init__.py` o import e as entradas de `__all__`:

```python
from horta.models.catalogo import (
    CatalogoValor,
    CatalogoVersion,
    CultivoSiex,
    NomeGalego,
    VariedadeLocal,
    VariedadeSiex,
)
```
e en `__all__`: `"CatalogoVersion", "CatalogoValor", "CultivoSiex", "VariedadeSiex", "NomeGalego", "VariedadeLocal",`.

- [ ] **Step 4: Executar os tests**

Run: `uv run pytest tests/models/test_catalogo.py -v`
Expected: 3 passed

- [ ] **Step 5: Migración**

Run: `uv run alembic revision --autogenerate -m "catalogos siex e capa galega"`
Revisar que o ficheiro xerado só crea as 6 táboas novas (sen tocar outras). Probar sobre BD baleira e sobre unha copia da BD de desenvolvemento:
```bash
cp horta.db /tmp/horta-proba.db && HORTA_DATABASE_URL=sqlite:////tmp/horta-proba.db uv run alembic upgrade head
```
Expected: sen erros.

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/catalogo.py src/horta/models/__init__.py alembic/versions tests/models/test_catalogo.py
git commit -m "feat: modelos de catálogos SIEX con versión e capa galega"
```

---

### Task 2: Importador de catálogos (Claude)

**Files:**
- Modify: `pyproject.toml` (dependencia `openpyxl`)
- Create: `src/horta/services/catalogos_importar.py`
- Test: `tests/services/test_catalogos_importar.py`

**Interfaces:**
- Consumes: modelos da Tarefa 1.
- Produces:
  - `CATALOGOS_XERAIS: dict[str, tuple[str, str, str | None]]` (clave interna → (ficheiro FEGA sen extensión, columna do código, columna de descrición ou None = 2ª columna))
  - `@dataclass InformeImportacion(catalogo: str, altas: int, baixas: int, cambios: int, xa_importado: bool)`
  - `importar_catalogo(session: Session, catalogo: str, ruta: Path, hoxe: date | None = None) -> InformeImportacion`
  - `importar_cultivos(session: Session, ruta: Path, hoxe: date | None = None) -> InformeImportacion`
  - `importar_variedades(session: Session, ruta: Path, hoxe: date | None = None) -> InformeImportacion`

- [ ] **Step 1: Engadir a dependencia**

Run: `uv add openpyxl`
Expected: `pyproject.toml` inclúe `openpyxl` en `dependencies`.

- [ ] **Step 2: Escribir os tests que fallan**

```python
# tests/services/test_catalogos_importar.py
from datetime import date
from pathlib import Path

from openpyxl import Workbook

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex
from horta.services.catalogos_importar import (
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)

_CAB_PRAGAS = ["Código SIEX", "Código", "Categoría", "Nombre científico", "EPPO cd",
               "Observaciones", "Fecha de alta", "Fecha de modificación", "Fecha de baja"]


def _xlsx(ruta: Path, cabeceira: list[str], filas: list[list]) -> Path:
    wb = Workbook()
    ws = wb.active
    ws.append(cabeceira)
    for fila in filas:
        ws.append(fila)
    wb.save(ruta)
    return ruta


def test_importa_altas_con_eppo_e_categoria(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", "30/06/2023", None, None],
        ["2", "7", "Insectos", "Insecta", "1INSEC", "", "30/06/2023", None, None],
    ])
    informe = importar_catalogo(session, "praga", f)
    assert (informe.altas, informe.baixas, informe.cambios) == (2, 0, 0)
    valor = session.query(CatalogoValor).filter_by(catalogo="praga", codigo="1").one()
    assert valor.descricion == "Arthropoda"
    assert valor.codigo_eppo == "1ARTHP"
    assert valor.categoria == "Artrópodos"
    assert valor.data_alta == date(2023, 6, 30)


def test_mesmo_ficheiro_dúas_veces_non_cambia_nada(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS,
              [["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", None, None, None]])
    importar_catalogo(session, "praga", f)
    informe = importar_catalogo(session, "praga", f)
    assert informe.xa_importado is True
    assert session.query(CatalogoVersion).count() == 1


def test_codigo_que_desaparece_queda_de_baixa_non_se_borra(session, tmp_path):
    f1 = _xlsx(tmp_path / "v1.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda", "1ARTHP", "", None, None, None],
        ["2", "7", "Insectos", "Insecta", "1INSEC", "", None, None, None],
    ])
    importar_catalogo(session, "praga", f1)
    f2 = _xlsx(tmp_path / "v2.xlsx", _CAB_PRAGAS, [
        ["1", "6", "Artrópodos", "Arthropoda nova", "1ARTHP", "", None, None, None],
    ])
    informe = importar_catalogo(session, "praga", f2, hoxe=date(2026, 11, 1))
    assert (informe.altas, informe.baixas, informe.cambios) == (0, 1, 1)
    dous = session.query(CatalogoValor).filter_by(catalogo="praga", codigo="2").one()
    assert dous.data_baixa == date(2026, 11, 1)
    assert session.query(CatalogoValor).filter_by(catalogo="praga").count() == 2


def test_baixa_oficial_do_ficheiro(session, tmp_path):
    f = _xlsx(tmp_path / "PLAGAS.xlsx", _CAB_PRAGAS,
              [["1", "6", "A", "Arthropoda", "", "", None, None, "15/03/2025"]])
    importar_catalogo(session, "praga", f)
    valor = session.query(CatalogoValor).one()
    assert valor.data_baixa == date(2025, 3, 15)


def test_catalogo_con_columna_de_descricion_por_defecto(session, tmp_path):
    f = _xlsx(tmp_path / "UNIDADES_MEDIDA.xlsx",
              ["Código SIEX", "Unidades de medida", "Fecha de alta", "Fecha de modificación",
               "Fecha de baja"],
              [["1", "m2", "20/09/2023", None, None]])
    importar_catalogo(session, "unidade_medida", f)
    assert session.query(CatalogoValor).one().descricion == "m2"


def test_catalogo_con_outra_columna_de_codigo(session, tmp_path):
    f = _xlsx(tmp_path / "TIPO_MAQUINA_UNE.xlsx", ["Código UNE", "Descripción"],
              [["0000000_88", "Máquinas sin clasificar"]])
    importar_catalogo(session, "tipo_maquinaria_une", f)
    assert session.query(CatalogoValor).one().codigo == "0000000_88"


def test_importa_cultivos_e_variedades(session, tmp_path):
    fc = _xlsx(tmp_path / "PRODUCTOS.xlsx",
               ["Código", "Cultivo", "Latín", "EPPO", "C. UPOV", "Hortícola", "Integrado",
                "Fecha de alta", "Fecha de modificación", "Fecha de baja"],
               [["99", "PATATA", "Solanum tuberosum", "SOLTU", "SOLAN_TUB", "SI", "SI",
                 "30/06/2023", None, None]])
    importar_cultivos(session, fc)
    pataca = session.get(CultivoSiex, 99)
    assert pataca is not None and pataca.codigo_eppo == "SOLTU" and pataca.horticola is True
    fv = _xlsx(tmp_path / "VARIEDAD_ESPECIE_TIPO.xlsx",
               ["Código cultivo", "Cultivo", "Latín", "EPPO", "C. UPOV",
                "Código Variedad/ Especie/ Tipo", "Variedad/ Especie/ Tipo",
                "Admisible Ayudas Asociadas", "Vinificable", "Integrado", "Fecha de alta",
                "Fecha de modificación", "Fecha de baja"],
               [["99", "PATATA", "", "", "", "0", "SIN VARIEDAD", "NO", "NO", "SI", None, None,
                 None],
                ["99", "PATATA", "", "", "", "12", "KENNEBEC", "NO", "NO", "SI", None, None,
                 None]])
    informe = importar_variedades(session, fv)
    assert informe.altas == 2
    assert session.query(VariedadeSiex).filter_by(cultivo_codigo=99, codigo=12).one() \
        .nome_oficial == "KENNEBEC"
```

- [ ] **Step 3: Executar e ver que fallan**

Run: `uv run pytest tests/services/test_catalogos_importar.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'horta.services.catalogos_importar'`

- [ ] **Step 4: Implementar o importador**

```python
# src/horta/services/catalogos_importar.py
"""Importación dos catálogos oficiais do FEGA (portal público SIEX, XLSX).

Idempotente: o mesmo ficheiro (mesmo sha256) non se reimporta. Nunca borra
códigos: os que desaparecen quedan con data_baixa (conservación legal).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, VariedadeSiex

# clave interna -> (ficheiro no portal FEGA, columna do código, columna da descrición;
# None = 2ª columna). Verificado contra os ficheiros descargados o 2026-10-22.
CATALOGOS_XERAIS: dict[str, tuple[str, str, str | None]] = {
    "praga": ("PLAGAS", "Código SIEX", "Nombre científico"),
    "enfermidade": ("ENFERMEDADES", "Código SIEX", "Nombre científico"),
    "mala_herba": ("MALAS_HIERBAS", "Código SIEX", "Nombre científico"),
    "regulador": ("REGULADORES_CRECIMIENTO", "Código SIEX",
                  "Nombre científico / Denominación en inglés"),
    "xustificacion": ("JUSTIFICACION_ACTUACION", "Código SIEX", None),
    "estado_fenoloxico": ("EST_FENOLOGICO", "Código SIEX", "Estado fenológico"),
    "unidade_medida": ("UNIDADES_MEDIDA", "Código SIEX", None),
    "eficacia": ("EFICACIA_TRATAMIENTO", "Código SIEX", None),
    "tipo_produto": ("TIPO_PRODFITO", "Código SIEX", None),
    "tipo_medida_fito": ("TIPO_MEDIDA_FITOSANITARIA", "Código SIEX", None),
    "tipo_maquinaria_une": ("TIPO_MAQUINA_UNE", "Código UNE", None),
    "tipo_enerxia": ("TIPENERGIA", "Código", None),
    "boas_practicas": ("BUENAS_PRACTICAS_AMBITOS", "Código SIEX", None),
}


@dataclass
class InformeImportacion:
    catalogo: str
    altas: int = 0
    baixas: int = 0
    cambios: int = 0
    xa_importado: bool = False


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


def _ler_xlsx(ruta: Path) -> tuple[list[str], list[dict[str, Any]]]:
    wb = load_workbook(ruta, read_only=False, data_only=True)
    ws = wb.active
    filas = [f for f in ws.iter_rows(values_only=True) if any(c is not None for c in f)]
    cabeceira = [str(c).strip() if c is not None else "" for c in filas[0]]
    return cabeceira, [dict(zip(cabeceira, f)) for f in filas[1:]]


def _data(valor: Any) -> date | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return datetime.strptime(str(valor).strip(), "%d/%m/%Y").date()


def _texto(valor: Any) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _codigo(valor: Any) -> str:
    texto = str(valor).strip()
    return texto[:-2] if texto.endswith(".0") else texto


def _nova_version(
    session: Session, catalogo: str, ruta: Path, filas: int
) -> CatalogoVersion | None:
    sha = _sha256(ruta)
    if session.query(CatalogoVersion).filter_by(catalogo=catalogo, sha256=sha).first():
        return None
    version = CatalogoVersion(catalogo=catalogo, nome_ficheiro=ruta.name, sha256=sha, filas=filas)
    session.add(version)
    session.flush()
    return version


def importar_catalogo(
    session: Session, catalogo: str, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    if catalogo not in CATALOGOS_XERAIS:
        raise ValueError(f"Catálogo descoñecido: {catalogo}")
    hoxe = hoxe or date.today()
    _, columna_codigo, columna_descricion = CATALOGOS_XERAIS[catalogo]
    cabeceira, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo=catalogo)
    version = _nova_version(session, catalogo, ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    columna = columna_descricion or cabeceira[1]
    existentes = {v.codigo: v for v in session.query(CatalogoValor).filter_by(catalogo=catalogo)}
    vistos: set[str] = set()
    for fila in filas:
        codigo = _codigo(fila[columna_codigo])
        vistos.add(codigo)
        datos = {
            "descricion": _texto(fila.get(columna)) or "",
            "codigo_eppo": _texto(fila.get("EPPO cd")),
            "categoria": _texto(fila.get("Categoría")),
            "data_alta": _data(fila.get("Fecha de alta")),
            "data_baixa": _data(fila.get("Fecha de baja")),
        }
        actual = existentes.get(codigo)
        if actual is None:
            session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, version_id=version.id,
                                      **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
    for codigo, valor in existentes.items():
        if codigo not in vistos and valor.data_baixa is None:
            valor.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe


def importar_cultivos(
    session: Session, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    hoxe = hoxe or date.today()
    _, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo="cultivo")
    version = _nova_version(session, "cultivo", ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    existentes = {c.codigo: c for c in session.query(CultivoSiex)}
    vistos: set[int] = set()
    for fila in filas:
        codigo = int(_codigo(fila["Código"]))
        vistos.add(codigo)
        datos = {
            "nome_oficial": _texto(fila.get("Cultivo")) or "",
            "nome_latin": _texto(fila.get("Latín")),
            "codigo_eppo": _texto(fila.get("EPPO")),
            "codigo_upov": _texto(fila.get("C. UPOV")),
            "horticola": _texto(fila.get("Hortícola")) == "SI",
            "integrado": _texto(fila.get("Integrado")) == "SI",
            "data_alta": _data(fila.get("Fecha de alta")),
            "data_baixa": _data(fila.get("Fecha de baja")),
        }
        actual = existentes.get(codigo)
        if actual is None:
            session.add(CultivoSiex(codigo=codigo, version_id=version.id, **datos))
            informe.altas += 1
        elif any(getattr(actual, k) != v for k, v in datos.items()):
            for k, v in datos.items():
                setattr(actual, k, v)
            actual.version_id = version.id
            informe.cambios += 1
    for codigo, cultivo in existentes.items():
        if codigo not in vistos and cultivo.data_baixa is None:
            cultivo.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe


def importar_variedades(
    session: Session, ruta: Path, hoxe: date | None = None
) -> InformeImportacion:
    hoxe = hoxe or date.today()
    _, filas = _ler_xlsx(ruta)
    informe = InformeImportacion(catalogo="variedade")
    version = _nova_version(session, "variedade", ruta, len(filas))
    if version is None:
        informe.xa_importado = True
        return informe
    cultivos = {c for (c,) in session.query(CultivoSiex.codigo)}
    existentes = {(v.cultivo_codigo, v.codigo): v for v in session.query(VariedadeSiex)}
    vistos: set[tuple[int, int]] = set()
    for fila in filas:
        cultivo = int(_codigo(fila["Código cultivo"]))
        if cultivo not in cultivos:
            continue  # variedade dun cultivo que non está no catálogo de cultivos
        clave = (cultivo, int(_codigo(fila["Código Variedad/ Especie/ Tipo"])))
        vistos.add(clave)
        nome = _texto(fila.get("Variedad/ Especie/ Tipo")) or ""
        baixa = _data(fila.get("Fecha de baja"))
        actual = existentes.get(clave)
        if actual is None:
            session.add(VariedadeSiex(cultivo_codigo=clave[0], codigo=clave[1], nome_oficial=nome,
                                      data_baixa=baixa, version_id=version.id))
            informe.altas += 1
        elif actual.nome_oficial != nome or actual.data_baixa != baixa:
            actual.nome_oficial, actual.data_baixa, actual.version_id = nome, baixa, version.id
            informe.cambios += 1
    for clave, variedade in existentes.items():
        if clave not in vistos and variedade.data_baixa is None:
            variedade.data_baixa = hoxe
            informe.baixas += 1
    session.commit()
    return informe
```

Nota: os cultivos impórtanse **antes** que as variedades (as variedades dun cultivo descoñecido ignóranse).

- [ ] **Step 5: Executar os tests**

Run: `uv run pytest tests/services/test_catalogos_importar.py -v`
Expected: 7 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock src/horta/services/catalogos_importar.py tests/services/test_catalogos_importar.py
git commit -m "feat: importador idempotente dos catálogos do FEGA"
```

---

### Task 3: Consultas de catálogos e capa galega (Claude)

**Files:**
- Create: `src/horta/services/catalogos.py`
- Create: `src/horta/data/nomes_galegos.csv`
- Test: `tests/services/test_catalogos.py`

**Interfaces:**
- Consumes: modelos da Tarefa 1.
- Produces:
  - `valores_vixentes(session, catalogo: str, na_data: date | None = None) -> list[CatalogoValor]`
  - `validar_codigo(session, catalogo: str, codigo: str, na_data: date) -> CatalogoValor` (lanza `OperacionNonPermitidaError`)
  - `describir(session, catalogo: str, codigo: str) -> str` (inclúe códigos de baixa; se non existe devolve o código)
  - `normalizar(texto: str) -> str` (minúsculas, sen acentos)
  - `buscar_cultivos(session, texto: str, limite: int = 20) -> list[tuple[CultivoSiex, str]]` (cultivo e nome a amosar; galego primeiro, por prioridade)
  - `cargar_nomes_galegos(session, ruta: Path) -> int`

- [ ] **Step 1: Escribir os tests que fallan**

```python
# tests/services/test_catalogos.py
from datetime import date
from pathlib import Path

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion, CultivoSiex, NomeGalego
from horta.services.catalogos import (
    buscar_cultivos,
    cargar_nomes_galegos,
    describir,
    normalizar,
    validar_codigo,
    valores_vixentes,
)
from horta.services.errors import OperacionNonPermitidaError


def _preparar(session):
    v = CatalogoVersion(catalogo="x", nome_ficheiro="x", sha256="b" * 64, filas=0)
    session.add(v)
    session.flush()
    session.add_all([
        CatalogoValor(catalogo="praga", codigo="1", descricion="Arthropoda", version_id=v.id),
        CatalogoValor(catalogo="praga", codigo="2", descricion="Vella", version_id=v.id,
                      data_baixa=date(2026, 1, 1)),
        CultivoSiex(codigo=99, nome_oficial="PATATA", version_id=v.id),
        CultivoSiex(codigo=484, nome_oficial="GRELOS", version_id=v.id),
        CultivoSiex(codigo=1, nome_oficial="TRIGO BLANDO", version_id=v.id),
    ])
    session.add(NomeGalego(catalogo="cultivo", codigo="99", nome_gl="Pataca", prioridade=10))
    session.commit()


def test_valores_vixentes_exclúe_os_de_baixa(session):
    _preparar(session)
    codigos = [v.codigo for v in valores_vixentes(session, "praga", date(2026, 6, 1))]
    assert codigos == ["1"]
    codigos_antes = [v.codigo for v in valores_vixentes(session, "praga", date(2025, 6, 1))]
    assert codigos_antes == ["1", "2"]


def test_validar_codigo_de_baixa_falla(session):
    _preparar(session)
    with pytest.raises(OperacionNonPermitidaError, match="non existe ou está de baixa"):
        validar_codigo(session, "praga", "2", date(2026, 6, 1))
    assert validar_codigo(session, "praga", "2", date(2025, 6, 1)).descricion == "Vella"


def test_describir_inclúe_baixas_e_descoñecidos(session):
    _preparar(session)
    assert describir(session, "praga", "2") == "Vella"
    assert describir(session, "praga", "999") == "999"


def test_normalizar():
    assert normalizar("  Ácaros ÑÁÉ ") == "acaros nae"


def test_buscar_cultivos_galego_primeiro(session):
    _preparar(session)
    resultado = buscar_cultivos(session, "pat")
    assert [(c.codigo, nome) for c, nome in resultado] == [(99, "Pataca")]
    resultado = buscar_cultivos(session, "")
    assert resultado[0][0].codigo == 99  # o de maior prioridade galega, primeiro


def test_cargar_nomes_galegos(session, tmp_path: Path):
    _preparar(session)
    ruta = tmp_path / "nomes.csv"
    ruta.write_text("codigo;nome_gl;prioridade\n484;Grelos;9\n", encoding="utf-8")
    assert cargar_nomes_galegos(session, ruta) == 1
    assert session.query(NomeGalego).filter_by(codigo="484").one().prioridade == 9
```

- [ ] **Step 2: Executar e ver que fallan**

Run: `uv run pytest tests/services/test_catalogos.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'horta.services.catalogos'`

- [ ] **Step 3: Implementar**

```python
# src/horta/services/catalogos.py
from __future__ import annotations

import csv
import unicodedata
from datetime import date
from pathlib import Path

from sqlalchemy import or_
from sqlalchemy.orm import Session

from horta.models.catalogo import CatalogoValor, CultivoSiex, NomeGalego
from horta.services.errors import OperacionNonPermitidaError


def normalizar(texto: str) -> str:
    sen_acentos = unicodedata.normalize("NFKD", texto.strip().lower())
    return "".join(c for c in sen_acentos if not unicodedata.combining(c))


def _vixente(na_data: date):
    return or_(CatalogoValor.data_baixa.is_(None), CatalogoValor.data_baixa > na_data)


def valores_vixentes(
    session: Session, catalogo: str, na_data: date | None = None
) -> list[CatalogoValor]:
    na_data = na_data or date.today()
    valores = (
        session.query(CatalogoValor)
        .filter(CatalogoValor.catalogo == catalogo, _vixente(na_data))
        .all()
    )
    return sorted(valores, key=lambda v: (len(v.codigo), v.codigo))


def validar_codigo(session: Session, catalogo: str, codigo: str, na_data: date) -> CatalogoValor:
    valor = (
        session.query(CatalogoValor)
        .filter(CatalogoValor.catalogo == catalogo, CatalogoValor.codigo == codigo,
                _vixente(na_data))
        .first()
    )
    if valor is None:
        raise OperacionNonPermitidaError(
            f"O código {codigo} non existe ou está de baixa no catálogo {catalogo}"
        )
    return valor


def describir(session: Session, catalogo: str, codigo: str) -> str:
    valor = session.query(CatalogoValor).filter_by(catalogo=catalogo, codigo=codigo).first()
    return valor.descricion if valor else codigo


def buscar_cultivos(
    session: Session, texto: str, limite: int = 20
) -> list[tuple[CultivoSiex, str]]:
    nomes = {
        int(n.codigo): (n.nome_gl, n.prioridade)
        for n in session.query(NomeGalego).filter_by(catalogo="cultivo")
    }
    buscado = normalizar(texto)
    resultado: list[tuple[int, str, CultivoSiex]] = []
    for cultivo in session.query(CultivoSiex).filter(CultivoSiex.data_baixa.is_(None)):
        nome_gl, prioridade = nomes.get(cultivo.codigo, (None, 0))
        nome = nome_gl or cultivo.nome_oficial.capitalize()
        candidatos = [normalizar(nome), normalizar(cultivo.nome_oficial)]
        if not buscado or any(buscado in c for c in candidatos):
            resultado.append((-prioridade, normalizar(nome), cultivo))
    resultado.sort(key=lambda r: (r[0], r[1]))
    return [(c, nomes.get(c.codigo, (None, 0))[0] or c.nome_oficial.capitalize())
            for _, _, c in resultado[:limite]]


def cargar_nomes_galegos(session: Session, ruta: Path) -> int:
    """Carga/actualiza nomes galegos de cultivos dende un CSV `codigo;nome_gl;prioridade`."""
    contador = 0
    with ruta.open(encoding="utf-8") as ficheiro:
        for fila in csv.DictReader(ficheiro, delimiter=";"):
            codigo = fila["codigo"].strip()
            nome = session.query(NomeGalego).filter_by(catalogo="cultivo", codigo=codigo).first()
            if nome is None:
                nome = NomeGalego(catalogo="cultivo", codigo=codigo)
                session.add(nome)
            nome.nome_gl = fila["nome_gl"].strip()
            nome.prioridade = int(fila["prioridade"])
            contador += 1
    session.commit()
    return contador
```

- [ ] **Step 4: Crear o CSV inicial de nomes galegos**

`src/horta/data/nomes_galegos.csv` (códigos verificados contra o catálogo PRODUCTOS do FEGA descargado o 2026-10-22; **antes de gardar, comprobar cada código** co script do Step 5):

```text
codigo;nome_gl;prioridade
99;Pataca;10
484;Grelos;10
179;Nabo;9
175;Berza;9
212;Kiwi;9
117;Castiñeiro;8
152;Pemento;9
```

O resto de cultivos habituais en Galicia (millo, vide, tomate, cebola, leituga, cabaza, faba, maceira, pereira, pradeira, etc.) engádense no mesmo formato, cos códigos que devolva o Step 5.

- [ ] **Step 5: Verificar códigos no catálogo real**

```bash
uv run python -I -c "
import openpyxl,sys
ws=openpyxl.load_workbook(sys.argv[1]).active
for r in ws.iter_rows(min_row=2,values_only=True):
    if r[1] and any(k in r[1].upper() for k in sys.argv[2:]): print(r[0], r[1], r[3])
" ../.playwright-mcp/fega/PRODUCTOS.xlsx MAIZ VID TOMATE CEBOLLA LECHUGA CALABAZA JUDIA MANZANO PERAL PRADO
```
Engadir as liñas ao CSV coa prioridade 7–8.

- [ ] **Step 6: Executar os tests**

Run: `uv run pytest tests/services/test_catalogos.py -v`
Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add src/horta/services/catalogos.py src/horta/data/nomes_galegos.csv tests/services/test_catalogos.py
git commit -m "feat: consultas de catálogos e nomes galegos de cultivos"
```

---

### Task 4: Persoas (aplicadores e asesores) — candidata para smoth

Claude implementa o modelo e a migración; o servizo e os tests pódense pasar a smoth como tarefa literal (o código completo está aquí).

**Files:**
- Create: `src/horta/models/persoa.py`
- Modify: `src/horta/models/__init__.py`
- Create: `src/horta/services/persoas.py`
- Test: `tests/services/test_persoas.py`

**Interfaces:**
- Produces:
  - `TipoCarne(enum)`: `basico, cualificado, fumigador, piloto, sector_suministrador, sector_tratamentos`
  - `Persoa` (táboa `persoa`): `id, horta_id, nome, apelidos, nif, e_aplicador, e_asesor, ropo_numero, ropo_tipo_carne, ropo_caducidade, regfer_numero, activa`
  - `crear_persoa(session, actor, horta_id, nome, **campos) -> Persoa`
  - `actualizar_persoa(session, actor, persoa, **cambios) -> Persoa`
  - `listar_persoas(session, actor, horta_id, so_activas=True) -> list[Persoa]`
  - `ropo_vixente(persoa, na_data: date) -> bool`

- [ ] **Step 1: Test que falla**

```python
# tests/services/test_persoas.py
from datetime import date

import pytest

from horta.models.horta import RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.errors import PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.persoas import actualizar_persoa, crear_persoa, listar_persoas, ropo_vixente


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(nome=email.split("@")[0], email=email, password_hash="hash-falso",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_aplicador_con_ropo(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan", apelidos="Pérez", nif="12345678z",
                          e_aplicador=True, ropo_numero="1234567890",
                          ropo_caducidade=date(2027, 5, 1))
    assert persoa.nif == "12345678Z"
    assert [p.nome for p in listar_persoas(session, ana, horta.id)] == ["Xan"]


def test_aplicador_sen_ropo_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="nº ROPO e a data de caducidade"):
        crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True)


def test_nif_mal_formado_rexeitase(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="NIF non é válido"):
        crear_persoa(session, ana, horta.id, "Xan", nif="123")


def test_lector_non_pode_crear(session):
    ana = _crear_usuario(session, "ana@example.com")
    carlos = _crear_usuario(session, "carlos@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_persoa(session, carlos, horta.id, "Xan")


def test_ropo_vixente_ata_o_dia_de_caducidade_incluido(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
                          ropo_caducidade=date(2026, 6, 1))
    assert ropo_vixente(persoa, date(2026, 6, 1)) is True
    assert ropo_vixente(persoa, date(2026, 6, 2)) is False


def test_desactivar_persoa(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    persoa = crear_persoa(session, ana, horta.id, "Xan")
    actualizar_persoa(session, ana, persoa, activa=False)
    assert listar_persoas(session, ana, horta.id) == []
    assert len(listar_persoas(session, ana, horta.id, so_activas=False)) == 1
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/services/test_persoas.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'horta.services.persoas'`

- [ ] **Step 3: Modelo**

```python
# src/horta/models/persoa.py
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class TipoCarne(enum.Enum):
    basico = "basico"
    cualificado = "cualificado"
    fumigador = "fumigador"
    piloto = "piloto"
    sector_suministrador = "sector_suministrador"
    sector_tratamentos = "sector_tratamentos"


class Persoa(Base):
    __tablename__ = "persoa"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    apelidos: Mapped[str | None] = mapped_column(String(200), default=None)
    nif: Mapped[str | None] = mapped_column(String(9), default=None)
    e_aplicador: Mapped[bool] = mapped_column(Boolean, default=False)
    e_asesor: Mapped[bool] = mapped_column(Boolean, default=False)
    ropo_numero: Mapped[str | None] = mapped_column(String(14), default=None)
    ropo_tipo_carne: Mapped[TipoCarne | None] = mapped_column(Enum(TipoCarne), default=None)
    ropo_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    regfer_numero: Mapped[str | None] = mapped_column(String(20), default=None)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
```

Engadir `from horta.models.persoa import Persoa, TipoCarne` e `"Persoa", "TipoCarne"` en `__all__` de `src/horta/models/__init__.py`.

- [ ] **Step 4: Servizo**

```python
# src/horta/services/persoas.py
from __future__ import annotations

import re
from datetime import date
from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.persoa import Persoa
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}

# Patrón oficial do descritor SIEX (Anexo VI, folla "Patrones texto") para NIF de persoa física.
_PATRON_NIF = re.compile(r"^[KLMXYZ0-9]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$")

CAMPOS_EDITABLES_PERSOA = frozenset(
    {"nome", "apelidos", "nif", "e_aplicador", "e_asesor", "ropo_numero", "ropo_tipo_carne",
     "ropo_caducidade", "regfer_numero", "activa"}
)


def _normalizar_e_validar(datos: dict[str, Any]) -> None:
    if datos.get("nif"):
        datos["nif"] = datos["nif"].strip().upper()
        if not _PATRON_NIF.match(datos["nif"]):
            raise OperacionNonPermitidaError("O NIF non é válido")
    if datos.get("e_aplicador") and not (datos.get("ropo_numero") and datos.get("ropo_caducidade")):
        raise OperacionNonPermitidaError(
            "Un aplicador precisa o nº ROPO e a data de caducidade do carné"
        )
    if datos.get("e_asesor") and not datos.get("ropo_numero"):
        raise OperacionNonPermitidaError("Un asesor precisa o nº ROPO")


def crear_persoa(
    session: Session, actor: Usuario, horta_id: int, nome: str, **campos: Any
) -> Persoa:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _normalizar_e_validar(campos)
    persoa = Persoa(horta_id=horta_id, nome=nome, **campos)
    session.add(persoa)
    session.commit()
    return persoa


def actualizar_persoa(session: Session, actor: Usuario, persoa: Persoa, **cambios: Any) -> Persoa:
    non_editables = set(cambios) - CAMPOS_EDITABLES_PERSOA
    if non_editables:
        raise ValueError(f"Campos non editables nunha persoa: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, persoa.horta_id, actor, _ROLES_ESCRITURA)
    resultado = {c: getattr(persoa, c) for c in CAMPOS_EDITABLES_PERSOA} | cambios
    _normalizar_e_validar(resultado)
    for campo in cambios:
        setattr(persoa, campo, resultado[campo])
    session.commit()
    return persoa


def listar_persoas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Persoa]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Persoa).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Persoa.nome).all())


def ropo_vixente(persoa: Persoa, na_data: date) -> bool:
    return persoa.ropo_caducidade is not None and persoa.ropo_caducidade >= na_data
```

- [ ] **Step 5: Executar os tests**

Run: `uv run pytest tests/services/test_persoas.py -v`
Expected: 6 passed

- [ ] **Step 6: Commit** (a migración vai na Tarefa 6, xunto coa de máquinas)

```bash
git add src/horta/models/persoa.py src/horta/models/__init__.py src/horta/services/persoas.py tests/services/test_persoas.py
git commit -m "feat: persoas da explotación con carné ROPO"
```

---

### Task 5: Maquinaria — candidata para smoth

**Files:**
- Create: `src/horta/models/maquina.py`
- Modify: `src/horta/models/__init__.py`
- Create: `src/horta/services/maquinaria.py`
- Test: `tests/services/test_maquinaria.py`

**Interfaces:**
- Produces:
  - `Maquina` (táboa `maquina`): `id, horta_id, alias, tipo_une (str|None, código catálogo "tipo_maquinaria_une"), marca_modelo, num_roma, num_reganip, id_equipo_non_inscribible, propia, potencia, unidade_potencia, tipo_enerxia, data_ultima_inspeccion, alugada, activa`
  - `crear_maquina(session, actor, horta_id, alias, **campos) -> Maquina`
  - `actualizar_maquina(session, actor, maquina, **cambios) -> Maquina`
  - `listar_maquinas(session, actor, horta_id, so_activas=True) -> list[Maquina]`

- [ ] **Step 1: Test que falla**

```python
# tests/services/test_maquinaria.py
import pytest

from horta.models.usuario import RolGlobal, Usuario
from horta.services.hortas import crear_horta
from horta.services.maquinaria import actualizar_maquina, crear_maquina, listar_maquinas


def _crear_usuario(session, email: str) -> Usuario:
    usuario = Usuario(nome=email.split("@")[0], email=email, password_hash="hash-falso",
                      rol=RolGlobal.USUARIO, activo=True)
    session.add(usuario)
    session.commit()
    return usuario


def test_crear_maquina_con_roma(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    maquina = crear_maquina(session, ana, horta.id, "Atomizador", num_roma="ES123456789")
    assert [m.alias for m in listar_maquinas(session, ana, horta.id)] == ["Atomizador"]
    assert maquina.propia is True


def test_so_un_identificador_permitido(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    with pytest.raises(ValueError, match="só un identificador"):
        crear_maquina(session, ana, horta.id, "Mochila", num_roma="A", num_reganip="B")


def test_actualizar_non_permite_dous_identificadores(session):
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    maquina = crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1")
    with pytest.raises(ValueError, match="só un identificador"):
        actualizar_maquina(session, ana, maquina, num_roma="ES1")
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/services/test_maquinaria.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Modelo**

```python
# src/horta/models/maquina.py
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Maquina(Base):
    __tablename__ = "maquina"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    alias: Mapped[str] = mapped_column(String(120))
    tipo_une: Mapped[str | None] = mapped_column(String(20), default=None)
    marca_modelo: Mapped[str | None] = mapped_column(String(200), default=None)
    num_roma: Mapped[str | None] = mapped_column(String(12), default=None)
    num_reganip: Mapped[str | None] = mapped_column(String(12), default=None)
    id_equipo_non_inscribible: Mapped[str | None] = mapped_column(String(50), default=None)
    propia: Mapped[bool] = mapped_column(Boolean, default=True)
    potencia: Mapped[float | None] = mapped_column(Float, default=None)
    unidade_potencia: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_enerxia: Mapped[str | None] = mapped_column(String(20), default=None)
    data_ultima_inspeccion: Mapped[date | None] = mapped_column(Date, default=None)
    alugada: Mapped[bool] = mapped_column(Boolean, default=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
```

Engadir `from horta.models.maquina import Maquina` e `"Maquina"` en `__all__`.

- [ ] **Step 4: Servizo**

```python
# src/horta/services/maquinaria.py
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from horta.models.horta import RolHorta
from horta.models.maquina import Maquina
from horta.models.usuario import Usuario
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}
_IDENTIFICADORES = ("num_roma", "num_reganip", "id_equipo_non_inscribible")

CAMPOS_EDITABLES_MAQUINA = frozenset(
    {"alias", "tipo_une", "marca_modelo", "num_roma", "num_reganip", "id_equipo_non_inscribible",
     "propia", "potencia", "unidade_potencia", "tipo_enerxia", "data_ultima_inspeccion", "alugada",
     "activa"}
)


def _validar(datos: dict[str, Any]) -> None:
    if sum(1 for c in _IDENTIFICADORES if datos.get(c)) > 1:
        raise OperacionNonPermitidaError(
            "Indica só un identificador: nº ROMA, nº REGANIP ou identificador do equipo"
        )


def crear_maquina(
    session: Session, actor: Usuario, horta_id: int, alias: str, **campos: Any
) -> Maquina:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    _validar(campos)
    maquina = Maquina(horta_id=horta_id, alias=alias, **campos)
    session.add(maquina)
    session.commit()
    return maquina


def actualizar_maquina(
    session: Session, actor: Usuario, maquina: Maquina, **cambios: Any
) -> Maquina:
    non_editables = set(cambios) - CAMPOS_EDITABLES_MAQUINA
    if non_editables:
        raise ValueError(f"Campos non editables nunha máquina: {', '.join(sorted(non_editables))}")
    comprobar_rol_horta(session, maquina.horta_id, actor, _ROLES_ESCRITURA)
    _validar({c: getattr(maquina, c) for c in _IDENTIFICADORES} | cambios)
    for campo, valor in cambios.items():
        setattr(maquina, campo, valor)
    session.commit()
    return maquina


def listar_maquinas(
    session: Session, actor: Usuario, horta_id: int, so_activas: bool = True
) -> list[Maquina]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    consulta = session.query(Maquina).filter_by(horta_id=horta_id)
    if so_activas:
        consulta = consulta.filter_by(activa=True)
    return list(consulta.order_by(Maquina.alias).all())
```

- [ ] **Step 5: Executar os tests**

Run: `uv run pytest tests/services/test_maquinaria.py -v`
Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/maquina.py src/horta/models/__init__.py src/horta/services/maquinaria.py tests/services/test_maquinaria.py
git commit -m "feat: maquinaria con ROMA/REGANIP"
```

---

### Task 6: Modelo do tratamento fitosanitario CUE e migración (Claude)

**Files:**
- Create: `src/horta/models/tratamento_fito.py`
- Modify: `src/horta/models/__init__.py`
- Create: `alembic/versions/<auto>_persoas_maquinas_tratamento_fito.py`
- Test: `tests/models/test_tratamento_fito.py`

**Interfaces:**
- Consumes: `Persoa`, `Maquina`, `Cultivo`.
- Produces (táboas e atributos):
  - `TratamentoFito` (`tratamento_fito`): `id, horta_id, data_inicio, data_fin, hora (time|None), actividade_cuberta (str|None), eficacia (str|None), observacions (str|None), baixa (bool), created_at, orixinal_produto, orixinal_dose, orixinal_aplicador, orixinal_equipo, orixinal_asesoramento, tratamento_antigo_id (int|None)`; relacións `cultivos, problemas, xustificacions, produtos, medidas, aplicadores, asesor` con `cascade="all, delete-orphan"`.
  - `TratamentoCultivo(tratamento_id, cultivo_id, superficie_ha, estado_fenoloxico)`
  - `TratamentoProblema(tratamento_id, tipo, codigo)`; `TipoProblema` = `enfermidade|praga|mala_herba|regulador` (o valor coincide coa clave do catálogo)
  - `TratamentoXustificacion(tratamento_id, codigo)`
  - `TratamentoProduto(tratamento_id, tipo_produto, num_rexistro, nome_comercial, materia_activa, dose, cantidade, unidade)`
  - `TratamentoMedida(tratamento_id, tipo_medida, cantidade, unidade, num_rexistro_mdf, boas_practicas)`
  - `TratamentoAplicador(tratamento_id, persoa_id, maquina_id, aplicacion_manual, horas_utilizacion, num_repeticions, duracion)`
  - `TratamentoAsesor(tratamento_id unique, persoa_id, data, validacion, observacions, confirmacion, contrato)`

- [ ] **Step 1: Test que falla**

```python
# tests/models/test_tratamento_fito.py
from datetime import date

from horta.models.tratamento_fito import (
    TratamentoCultivo,
    TratamentoFito,
    TratamentoProblema,
    TratamentoProduto,
)
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo
from horta.services.hortas import crear_horta
from horta.services.parcelas import crear_parcela


def test_tratamento_con_fillos_e_borrado_en_cascada_dos_fillos(session):
    ana = Usuario(nome="ana", email="ana@example.com", password_hash="x",
                  rol=RolGlobal.USUARIO, activo=True)
    session.add(ana)
    session.commit()
    horta = crear_horta(session, ana, "Horta")
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=1000.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    t = TratamentoFito(horta_id=horta.id, data_inicio=date(2026, 5, 1),
                       data_fin=date(2026, 5, 1))
    t.cultivos.append(TratamentoCultivo(cultivo_id=cultivo.id, superficie_ha=0.1))
    t.problemas.append(TratamentoProblema(tipo="enfermidade", codigo="10"))
    t.produtos.append(TratamentoProduto(tipo_produto="1", num_rexistro="ES-00001",
                                        nome_comercial="Cobre", dose=2.0, unidade="5"))
    session.add(t)
    session.commit()
    assert t.baixa is False
    t.produtos.clear()
    session.commit()
    assert session.query(TratamentoProduto).count() == 0
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/models/test_tratamento_fito.py -v`
Expected: FAIL con `ModuleNotFoundError`

- [ ] **Step 3: Modelos**

```python
# src/horta/models/tratamento_fito.py
"""Tratamento fitosanitario conforme ao bloque TratamFito do descritor CUE (FEGA v3.11.4)."""

from __future__ import annotations

from datetime import date, datetime, time, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base

TIPOS_PROBLEMA = ("enfermidade", "praga", "mala_herba", "regulador")


class TratamentoFito(Base):
    __tablename__ = "tratamento_fito"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    hora: Mapped[time | None] = mapped_column(Time, default=None)
    actividade_cuberta: Mapped[str | None] = mapped_column(String(20), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(20), default=None)
    observacions: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    orixinal_produto: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_dose: Mapped[str | None] = mapped_column(String(100), default=None)
    orixinal_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_equipo: Mapped[str | None] = mapped_column(String(200), default=None)
    orixinal_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    tratamento_antigo_id: Mapped[int | None] = mapped_column(Integer, default=None)

    cultivos: Mapped[list[TratamentoCultivo]] = relationship(cascade="all, delete-orphan")
    problemas: Mapped[list[TratamentoProblema]] = relationship(cascade="all, delete-orphan")
    xustificacions: Mapped[list[TratamentoXustificacion]] = relationship(
        cascade="all, delete-orphan"
    )
    produtos: Mapped[list[TratamentoProduto]] = relationship(cascade="all, delete-orphan")
    medidas: Mapped[list[TratamentoMedida]] = relationship(cascade="all, delete-orphan")
    aplicadores: Mapped[list[TratamentoAplicador]] = relationship(cascade="all, delete-orphan")
    asesor: Mapped[TratamentoAsesor | None] = relationship(
        cascade="all, delete-orphan", uselist=False
    )


class TratamentoCultivo(Base):
    __tablename__ = "tratamento_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    estado_fenoloxico: Mapped[str | None] = mapped_column(String(20), default=None)


class TratamentoProblema(Base):
    __tablename__ = "tratamento_problema"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(20))
    codigo: Mapped[str] = mapped_column(String(20))


class TratamentoXustificacion(Base):
    __tablename__ = "tratamento_xustificacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class TratamentoProduto(Base):
    __tablename__ = "tratamento_produto"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo_produto: Mapped[str] = mapped_column(String(20))
    num_rexistro: Mapped[str | None] = mapped_column(String(20), default=None)
    nome_comercial: Mapped[str | None] = mapped_column(String(200), default=None)
    materia_activa: Mapped[str | None] = mapped_column(String(200), default=None)
    dose: Mapped[float | None] = mapped_column(Float, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str] = mapped_column(String(20))


class TratamentoMedida(Base):
    __tablename__ = "tratamento_medida"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    tipo_medida: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    num_rexistro_mdf: Mapped[str | None] = mapped_column(String(10), default=None)
    boas_practicas: Mapped[str | None] = mapped_column(String(20), default=None)


class TratamentoAplicador(Base):
    __tablename__ = "tratamento_aplicador"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), index=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    aplicacion_manual: Mapped[bool] = mapped_column(Boolean, default=False)
    horas_utilizacion: Mapped[float | None] = mapped_column(Float, default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion: Mapped[float | None] = mapped_column(Float, default=None)


class TratamentoAsesor(Base):
    __tablename__ = "tratamento_asesor"

    id: Mapped[int] = mapped_column(primary_key=True)
    tratamento_id: Mapped[int] = mapped_column(ForeignKey("tratamento_fito.id"), unique=True)
    persoa_id: Mapped[int] = mapped_column(ForeignKey("persoa.id"))
    data: Mapped[date | None] = mapped_column(Date, default=None)
    validacion: Mapped[bool] = mapped_column(Boolean, default=False)
    observacions: Mapped[str | None] = mapped_column(String(200), default=None)
    confirmacion: Mapped[bool] = mapped_column(Boolean, default=False)
    contrato: Mapped[bool] = mapped_column(Boolean, default=False)
```

Engadir a `src/horta/models/__init__.py`:
```python
from horta.models.tratamento_fito import (
    TratamentoAplicador,
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoMedida,
    TratamentoProblema,
    TratamentoProduto,
    TratamentoXustificacion,
)
```
e os oito nomes en `__all__`.

- [ ] **Step 4: Executar o test**

Run: `uv run pytest tests/models/test_tratamento_fito.py -v`
Expected: 1 passed

- [ ] **Step 5: Migración de esquema + copia de datos**

Run: `uv run alembic revision --autogenerate -m "persoas maquinas e tratamento fito"`
Revisar que crea `persoa`, `maquina` e as 8 táboas de tratamento. Engadir ao final de `upgrade()` a copia dos tratamentos antigos:

```python
    # Copiar os tratamentos antigos ao novo modelo (sen inventar códigos).
    conn = op.get_bind()
    antigos = conn.execute(sa.text(
        "SELECT t.id, p.horta_id, t.data, t.superficie_tratada, t.cultivo_id, t.praga, "
        "t.produto, t.numero_rexistro_produto, t.dose, t.eficacia, t.aplicador, "
        "t.equipo_aplicador, t.persoas_asesoramento, t.notas, t.baixa, t.created_at "
        "FROM tratamento t JOIN cultivo c ON c.id = t.cultivo_id "
        "JOIN parcela p ON p.id = c.parcela_id"
    )).mappings().all()
    for t in antigos:
        observacions = "; ".join(
            x for x in [
                f"Praga (texto orixinal): {t['praga']}" if t["praga"] else "",
                f"Eficacia (texto orixinal): {t['eficacia']}" if t["eficacia"] else "",
                f"Nº rexistro orixinal: {t['numero_rexistro_produto']}"
                if t["numero_rexistro_produto"] else "",
                t["notas"] or "",
            ] if x
        ) or None
        resultado = conn.execute(sa.text(
            "INSERT INTO tratamento_fito (horta_id, data_inicio, data_fin, observacions, baixa, "
            "created_at, orixinal_produto, orixinal_dose, orixinal_aplicador, orixinal_equipo, "
            "orixinal_asesoramento, tratamento_antigo_id) VALUES (:h, :d, :d, :o, :b, :c, :pr, "
            ":do, :ap, :eq, :as, :id)"
        ), {"h": t["horta_id"], "d": t["data"], "o": observacions, "b": t["baixa"],
            "c": t["created_at"], "pr": t["produto"], "do": t["dose"], "ap": t["aplicador"],
            "eq": t["equipo_aplicador"], "as": t["persoas_asesoramento"], "id": t["id"]})
        novo_id = resultado.lastrowid
        superficie_ha = t["superficie_tratada"] / 10000 if t["superficie_tratada"] else None
        conn.execute(sa.text(
            "INSERT INTO tratamento_cultivo (tratamento_id, cultivo_id, superficie_ha) "
            "VALUES (:t, :c, :s)"
        ), {"t": novo_id, "c": t["cultivo_id"], "s": superficie_ha})
```

Nota: na app actual `superficie_tratada` está en m² (igual que `Parcela.superficie`); o CUE usa hectáreas, por iso se divide entre 10.000. **Comprobar** nos formularios actuais (`horta_detalle.py`, etiqueta "Superficie (m²)") antes de aplicar.

`downgrade()` só borra as táboas novas (os datos antigos seguen en `tratamento`).

Probar sobre copia da BD real:
```bash
cp horta.db /tmp/horta-proba.db && HORTA_DATABASE_URL=sqlite:////tmp/horta-proba.db uv run alembic upgrade head
sqlite3 /tmp/horta-proba.db "select count(*) from tratamento; select count(*) from tratamento_fito;"
```
Expected: as dúas contas iguais.

- [ ] **Step 6: Commit**

```bash
git add src/horta/models/tratamento_fito.py src/horta/models/__init__.py alembic/versions tests/models/test_tratamento_fito.py
git commit -m "feat: modelo de tratamento fitosanitario CUE e migración dos existentes"
```

---

### Task 6b: Ligar os cultivos da horta aos códigos oficiais (Claude)

**Files:**
- Modify: `src/horta/models/cultivo.py`, `src/horta/services/cultivos.py`
- Create: `alembic/versions/<auto>_cultivo_codigos_siex.py`
- Test: `tests/services/test_cultivos.py`

**Interfaces:**
- Produces: columnas `Cultivo.cultivo_siex_codigo: int | None` (FK `cultivo_siex.codigo`), `Cultivo.variedade_siex_id: int | None` (FK `variedade_siex.id`), `Cultivo.variedade_local_id: int | None` (FK `variedade_local.id`); editables en `actualizar_cultivo`.
- A Tarefa 7 compara `cultivo_siex_codigo` (e variedade) cando estean informados; se non, compara `especie`/`variedade` en texto (cultivos antigos e autoconsumo).

- [ ] **Step 1: Test que falla** (engadir ao final de `tests/services/test_cultivos.py`)

```python
def test_cultivo_ligado_ao_codigo_siex(session):
    from horta.models.catalogo import CatalogoVersion, CultivoSiex

    v = CatalogoVersion(catalogo="cultivo", nome_ficheiro="x", sha256="d" * 64, filas=1)
    session.add(v)
    session.flush()
    session.add(CultivoSiex(codigo=99, nome_oficial="PATATA", version_id=v.id))
    session.commit()
    ana = _crear_usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "A miña horta")
    parcela = crear_parcela(session, ana, horta.id, "Parcela Norte")
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca", cultivo_siex_codigo=99)
    assert cultivo.cultivo_siex_codigo == 99
    actualizar_cultivo(session, ana, cultivo, cultivo_siex_codigo=None)
    assert cultivo.cultivo_siex_codigo is None
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/services/test_cultivos.py -k siex -v`
Expected: FAIL (`TypeError: 'cultivo_siex_codigo' is an invalid keyword argument`)

- [ ] **Step 3: Implementar**

En `src/horta/models/cultivo.py`, clase `Cultivo`, despois de `variedade`:
```python
    cultivo_siex_codigo: Mapped[int | None] = mapped_column(
        ForeignKey("cultivo_siex.codigo"), default=None
    )
    variedade_siex_id: Mapped[int | None] = mapped_column(
        ForeignKey("variedade_siex.id"), default=None
    )
    variedade_local_id: Mapped[int | None] = mapped_column(
        ForeignKey("variedade_local.id"), default=None
    )
```
En `src/horta/services/cultivos.py`, engadir `"cultivo_siex_codigo", "variedade_siex_id", "variedade_local_id"` a `CAMPOS_EDITABLES_CULTIVO`.

Na Tarefa 7, `_validar` usa como clave de "mesmo cultivo" `(cultivo.cultivo_siex_codigo, cultivo.variedade_siex_id)` cando `cultivo_siex_codigo` non é `None`, e `(especie, variedade)` en texto se non:
```python
        if cultivo.cultivo_siex_codigo is not None:
            especies.add((str(cultivo.cultivo_siex_codigo), str(cultivo.variedade_siex_id)))
        else:
            especies.add((cultivo.especie.strip().lower(),
                          (cultivo.variedade or "").strip().lower()))
```

- [ ] **Step 4: Migración** — `uv run alembic revision --autogenerate -m "cultivo codigos siex"`; en SQLite engadir columnas con FK require `op.batch_alter_table("cultivo")`; revisar o ficheiro xerado e usar `with op.batch_alter_table("cultivo") as batch:` para as tres columnas. Probar sobre copia da BD.

- [ ] **Step 5: Tests e commit**

Run: `uv run pytest -q` → verde
```bash
git add src/horta/models/cultivo.py src/horta/services/cultivos.py alembic/versions tests/services/test_cultivos.py
git commit -m "feat: ligar cultivos aos códigos oficiais do SIEX"
```

No formulario de cultivos (fóra desta fase se non dá tempo) engadirase un selector con `buscar_cultivos`; mentres tanto, a Tarefa 10 amosa os cultivos pola súa especie.

---

### Task 7: Servizo de tratamentos fitosanitarios CUE (Claude)

**Files:**
- Create: `src/horta/services/tratamentos_fito.py`
- Modify: `src/horta/services/cultivos.py` (bloquear borrado), `src/horta/services/parcelas.py` (bloquear borrado)
- Test: `tests/services/test_tratamentos_fito.py`, e engadir tests a `tests/services/test_cultivos.py`

**Interfaces:**
- Consumes: Tarefas 3, 4, 5, 6.
- Produces:
  - dataclasses `LinhaCultivo(cultivo_id: int, superficie_ha: float | None, estado_fenoloxico: str | None = None)`, `Problema(tipo: str, codigo: str)`, `LinhaProduto(tipo_produto: str, unidade: str, num_rexistro: str | None = None, nome_comercial: str | None = None, materia_activa: str | None = None, dose: float | None = None, cantidade: float | None = None)`, `LinhaMedida(tipo_medida: str, cantidade: float | None = None, unidade: str | None = None, num_rexistro_mdf: str | None = None, boas_practicas: str | None = None)`, `LinhaAplicador(persoa_id: int, maquina_id: int | None = None, aplicacion_manual: bool = False, horas_utilizacion: float | None = None, num_repeticions: int | None = None, duracion: float | None = None)`, `DatosAsesor(persoa_id: int, data: date | None = None, validacion: bool = False, observacions: str | None = None, confirmacion: bool = False, contrato: bool = False)`, `DatosTratamento(data_inicio: date, data_fin: date, cultivos: list[LinhaCultivo], problemas: list[Problema], xustificacions: list[str], produtos: list[LinhaProduto], medidas: list[LinhaMedida], aplicadores: list[LinhaAplicador], hora: time | None = None, asesor: DatosAsesor | None = None, eficacia: str | None = None, observacions: str | None = None, actividade_cuberta: str | None = None)`
  - `crear_tratamento_fito(session, actor, horta_id, datos) -> TratamentoFito`
  - `actualizar_tratamento_fito(session, actor, tratamento, datos) -> TratamentoFito`
  - `dar_de_baixa_tratamento_fito(session, actor, tratamento) -> None`
  - `listar_tratamentos_fito(session, actor, horta_id) -> list[TratamentoFito]`
  - `faltas_para_cue(tratamento) -> list[str]`

- [ ] **Step 1: Tests que fallan**

```python
# tests/services/test_tratamentos_fito.py
from datetime import date

import pytest

from horta.models.catalogo import CatalogoValor, CatalogoVersion
from horta.models.horta import Horta, RolHorta
from horta.models.usuario import RolGlobal, Usuario
from horta.services.cultivos import crear_cultivo, eliminar_cultivo
from horta.services.errors import OperacionNonPermitidaError, PermisoDenegadoError
from horta.services.hortas import crear_horta, engadir_membro
from horta.services.maquinaria import crear_maquina
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_persoa
from horta.services.tratamentos_fito import (
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
    dar_de_baixa_tratamento_fito,
    faltas_para_cue,
    listar_tratamentos_fito,
)

D = date(2026, 5, 10)


def _usuario(session, email):
    u = Usuario(nome=email, email=email, password_hash="x", rol=RolGlobal.USUARIO, activo=True)
    session.add(u)
    session.commit()
    return u


def _catalogos(session):
    v = CatalogoVersion(catalogo="t", nome_ficheiro="t", sha256="c" * 64, filas=0)
    session.add(v)
    session.flush()
    for catalogo, codigo in [("enfermidade", "10"), ("xustificacion", "1"),
                             ("tipo_produto", "1"), ("unidade_medida", "5"),
                             ("estado_fenoloxico", "6"), ("eficacia", "1")]:
        session.add(CatalogoValor(catalogo=catalogo, codigo=codigo, descricion=catalogo,
                                  version_id=v.id))
    session.add(CatalogoValor(catalogo="enfermidade", codigo="99", descricion="vella",
                              version_id=v.id, data_baixa=date(2026, 1, 1)))
    session.commit()


def _escenario(session, profesional=True):
    _catalogos(session)
    ana = _usuario(session, "ana@example.com")
    horta = crear_horta(session, ana, "Horta")
    session.get(Horta, horta.id).uso_profesional = profesional
    session.commit()
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=2000.0)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    xan = crear_persoa(session, ana, horta.id, "Xan", e_aplicador=True, ropo_numero="1",
                       ropo_caducidade=D)
    maquina = crear_maquina(session, ana, horta.id, "Mochila", id_equipo_non_inscribible="M1")
    return ana, horta, parcela, cultivo, xan, maquina


def _datos(cultivo, xan, maquina, **cambios):
    base = dict(
        data_inicio=D, data_fin=D,
        cultivos=[LinhaCultivo(cultivo_id=cultivo.id, superficie_ha=0.1, estado_fenoloxico="6")],
        problemas=[Problema(tipo="enfermidade", codigo="10")],
        xustificacions=["1"],
        produtos=[LinhaProduto(tipo_produto="1", unidade="5", num_rexistro="ES-1",
                               nome_comercial="Cobre", dose=2.0)],
        medidas=[],
        aplicadores=[LinhaAplicador(persoa_id=xan.id, maquina_id=maquina.id)],
        eficacia="1",
    )
    base.update(cambios)
    return DatosTratamento(**base)


def test_crear_tratamento_completo(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    t = crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    assert [c.cultivo_id for c in t.cultivos] == [cultivo.id]
    assert faltas_para_cue(t) == []
    assert listar_tratamentos_fito(session, ana, horta.id) == [t]


def test_ropo_que_caduca_o_mesmo_dia_e_valido(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))


def test_ropo_caducado_bloquea(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    datos = _datos(cultivo, xan, maquina, data_inicio=date(2026, 5, 11),
                   data_fin=date(2026, 5, 11))
    with pytest.raises(OperacionNonPermitidaError, match="carné ROPO de Xan caducou"):
        crear_tratamento_fito(session, ana, horta.id, datos)


def test_data_fin_anterior_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="data de fin"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, data_fin=date(2026, 5, 9)))


def test_dose_e_cantidade_a_vez_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    produto = LinhaProduto(tipo_produto="1", unidade="5", num_rexistro="ES-1", dose=1.0,
                           cantidade=3.0)
    with pytest.raises(OperacionNonPermitidaError, match="dose ou a cantidade"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, produtos=[produto]))


def test_sen_produto_nin_medida_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="produto ou unha medida"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, produtos=[]))


def test_codigo_de_baixa_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="de baixa"):
        crear_tratamento_fito(
            session, ana, horta.id,
            _datos(cultivo, xan, maquina, problemas=[Problema(tipo="enfermidade",
                                                              codigo="99")]))


def test_cultivos_distintos_rexeitanse(session):
    ana, horta, parcela, cultivo, xan, maquina = _escenario(session)
    outro = crear_cultivo(session, ana, parcela.id, "Tomate")
    linhas = [LinhaCultivo(cultivo.id, 0.1), LinhaCultivo(outro.id, 0.1)]
    with pytest.raises(OperacionNonPermitidaError, match="mesmo cultivo"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, cultivos=linhas))


def test_superficie_maior_ca_parcela_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)  # parcela de 2000 m² = 0,2 ha
    linhas = [LinhaCultivo(cultivo.id, 0.5)]
    with pytest.raises(OperacionNonPermitidaError, match="maior ca da parcela"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, cultivos=linhas))


def test_cultivo_doutra_horta_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    outra = crear_horta(session, ana, "Outra")
    p2 = crear_parcela(session, ana, outra.id, "P2")
    c2 = crear_cultivo(session, ana, p2.id, "Pataca")
    with pytest.raises(OperacionNonPermitidaError, match="non pertence a esta horta"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina,
                                     cultivos=[LinhaCultivo(c2.id, 0.1)]))


def test_lector_non_pode_crear(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    carlos = _usuario(session, "carlos@example.com")
    engadir_membro(session, ana, horta.id, carlos, RolHorta.LECTOR)
    with pytest.raises(PermisoDenegadoError):
        crear_tratamento_fito(session, carlos, horta.id, _datos(cultivo, xan, maquina))


def test_autoconsumo_con_datos_minimos(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session, profesional=False)
    datos = _datos(cultivo, xan, maquina, xustificacions=[], aplicadores=[], eficacia=None)
    t = crear_tratamento_fito(session, ana, horta.id, datos)
    assert "aplicador" in " ".join(faltas_para_cue(t))


def test_profesional_sen_aplicador_rexeitase(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    with pytest.raises(OperacionNonPermitidaError, match="aplicador"):
        crear_tratamento_fito(session, ana, horta.id,
                              _datos(cultivo, xan, maquina, aplicadores=[]))


def test_baixa_loxica(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    t = crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    dar_de_baixa_tratamento_fito(session, ana, t)
    assert listar_tratamentos_fito(session, ana, horta.id) == []
    assert t.baixa is True


def test_non_se_pode_eliminar_cultivo_con_tratamentos(session):
    ana, horta, _, cultivo, xan, maquina = _escenario(session)
    crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    with pytest.raises(OperacionNonPermitidaError, match="tratamentos fitosanitarios"):
        eliminar_cultivo(session, ana, cultivo)
```

- [ ] **Step 2: Executar e ver que fallan**

Run: `uv run pytest tests/services/test_tratamentos_fito.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'horta.services.tratamentos_fito'`

- [ ] **Step 3: Implementar o servizo**

```python
# src/horta/services/tratamentos_fito.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time

from sqlalchemy.orm import Session

from horta.models.cultivo import Cultivo
from horta.models.horta import Horta, RolHorta
from horta.models.maquina import Maquina
from horta.models.parcela import Parcela
from horta.models.persoa import Persoa
from horta.models.tratamento_fito import (
    TIPOS_PROBLEMA,
    TratamentoAplicador,
    TratamentoAsesor,
    TratamentoCultivo,
    TratamentoFito,
    TratamentoMedida,
    TratamentoProblema,
    TratamentoProduto,
    TratamentoXustificacion,
)
from horta.models.usuario import Usuario
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
from horta.services.hortas import comprobar_rol_horta
from horta.services.persoas import ropo_vixente

_ROLES_ESCRITURA = {RolHorta.ADMIN, RolHorta.EDITOR}
_ROLES_LECTURA = {RolHorta.ADMIN, RolHorta.EDITOR, RolHorta.LECTOR}


@dataclass
class LinhaCultivo:
    cultivo_id: int
    superficie_ha: float | None
    estado_fenoloxico: str | None = None


@dataclass
class Problema:
    tipo: str
    codigo: str


@dataclass
class LinhaProduto:
    tipo_produto: str
    unidade: str
    num_rexistro: str | None = None
    nome_comercial: str | None = None
    materia_activa: str | None = None
    dose: float | None = None
    cantidade: float | None = None


@dataclass
class LinhaMedida:
    tipo_medida: str
    cantidade: float | None = None
    unidade: str | None = None
    num_rexistro_mdf: str | None = None
    boas_practicas: str | None = None


@dataclass
class LinhaAplicador:
    persoa_id: int
    maquina_id: int | None = None
    aplicacion_manual: bool = False
    horas_utilizacion: float | None = None
    num_repeticions: int | None = None
    duracion: float | None = None


@dataclass
class DatosAsesor:
    persoa_id: int
    data: date | None = None
    validacion: bool = False
    observacions: str | None = None
    confirmacion: bool = False
    contrato: bool = False


@dataclass
class DatosTratamento:
    data_inicio: date
    data_fin: date
    cultivos: list[LinhaCultivo]
    problemas: list[Problema]
    xustificacions: list[str]
    produtos: list[LinhaProduto] = field(default_factory=list)
    medidas: list[LinhaMedida] = field(default_factory=list)
    aplicadores: list[LinhaAplicador] = field(default_factory=list)
    hora: time | None = None
    asesor: DatosAsesor | None = None
    eficacia: str | None = None
    observacions: str | None = None
    actividade_cuberta: str | None = None


def _erro(mensaxe: str) -> OperacionNonPermitidaError:
    return OperacionNonPermitidaError(mensaxe)


def _validar(session: Session, horta: Horta, datos: DatosTratamento) -> None:
    profesional = horta.uso_profesional
    d = datos.data_inicio
    if datos.data_fin < datos.data_inicio:
        raise _erro("A data de fin non pode ser anterior á de inicio")
    if not datos.cultivos:
        raise _erro("Indica polo menos un cultivo tratado")
    especies: set[tuple[str, str | None]] = set()
    for linha in datos.cultivos:
        cultivo = session.get(Cultivo, linha.cultivo_id)
        parcela = session.get(Parcela, cultivo.parcela_id) if cultivo else None
        if cultivo is None or parcela is None or parcela.horta_id != horta.id:
            raise _erro("O cultivo indicado non pertence a esta horta")
        if cultivo.cultivo_siex_codigo is not None:
            especies.add((str(cultivo.cultivo_siex_codigo), str(cultivo.variedade_siex_id)))
        else:
            especies.add((cultivo.especie.strip().lower(),
                          (cultivo.variedade or "").strip().lower()))
        if linha.superficie_ha is not None:
            if linha.superficie_ha <= 0:
                raise _erro("A superficie tratada ten que ser maior que 0")
            if parcela.superficie and linha.superficie_ha > parcela.superficie / 10000:
                raise _erro(f"A superficie tratada é maior ca da parcela {parcela.nome}")
        if linha.estado_fenoloxico:
            validar_codigo(session, "estado_fenoloxico", linha.estado_fenoloxico, d)
    if len(especies) > 1:
        raise _erro("Todos os cultivos dun tratamento teñen que ser do mesmo cultivo e variedade")
    if not datos.problemas:
        raise _erro("Indica polo menos un problema (praga, enfermidade, mala herba ou regulador)")
    for problema in datos.problemas:
        if problema.tipo not in TIPOS_PROBLEMA:
            raise _erro(f"Tipo de problema descoñecido: {problema.tipo}")
        validar_codigo(session, problema.tipo, problema.codigo, d)
    if profesional and not datos.xustificacions:
        raise _erro("Indica polo menos unha xustificación do tratamento")
    for codigo in datos.xustificacions:
        validar_codigo(session, "xustificacion", codigo, d)
    if not datos.produtos and not datos.medidas:
        raise _erro("Indica polo menos un produto ou unha medida non química")
    for produto in datos.produtos:
        if (produto.dose is None) == (produto.cantidade is None):
            raise _erro("Indica a dose ou a cantidade do produto (só unha das dúas)")
        valor = produto.dose if produto.dose is not None else produto.cantidade
        if valor is not None and valor <= 0:
            raise _erro("A dose ou cantidade ten que ser maior que 0")
        validar_codigo(session, "tipo_produto", produto.tipo_produto, d)
        validar_codigo(session, "unidade_medida", produto.unidade, d)
        if profesional and produto.tipo_produto == "1" and not produto.num_rexistro:
            raise _erro("Os produtos fitosanitarios rexistrados precisan o nº de rexistro")
    for medida in datos.medidas:
        validar_codigo(session, "tipo_medida_fito", medida.tipo_medida, d)
    if profesional and not datos.aplicadores:
        raise _erro("Indica polo menos un aplicador")
    for linha_aplicador in datos.aplicadores:
        persoa = session.get(Persoa, linha_aplicador.persoa_id)
        if persoa is None or persoa.horta_id != horta.id or not persoa.e_aplicador:
            raise _erro("O aplicador indicado non é un aplicador desta horta")
        if profesional and not ropo_vixente(persoa, d):
            raise _erro(
                f"O carné ROPO de {persoa.nome} caducou o "
                f"{persoa.ropo_caducidade:%d/%m/%Y}" if persoa.ropo_caducidade
                else f"{persoa.nome} non ten data de caducidade do carné ROPO"
            )
        if linha_aplicador.maquina_id is not None:
            maquina = session.get(Maquina, linha_aplicador.maquina_id)
            if maquina is None or maquina.horta_id != horta.id:
                raise _erro("A máquina indicada non é desta horta")
    if datos.asesor is not None:
        asesor = session.get(Persoa, datos.asesor.persoa_id)
        if asesor is None or asesor.horta_id != horta.id or not asesor.e_asesor:
            raise _erro("O asesor indicado non é un asesor desta horta")
    if datos.eficacia:
        validar_codigo(session, "eficacia", datos.eficacia, d)


def _aplicar(tratamento: TratamentoFito, datos: DatosTratamento) -> None:
    tratamento.data_inicio = datos.data_inicio
    tratamento.data_fin = datos.data_fin
    tratamento.hora = datos.hora
    tratamento.eficacia = datos.eficacia
    tratamento.observacions = datos.observacions
    tratamento.actividade_cuberta = datos.actividade_cuberta
    tratamento.cultivos = [TratamentoCultivo(cultivo_id=c.cultivo_id, superficie_ha=c.superficie_ha,
                                             estado_fenoloxico=c.estado_fenoloxico)
                           for c in datos.cultivos]
    tratamento.problemas = [TratamentoProblema(tipo=p.tipo, codigo=p.codigo)
                            for p in datos.problemas]
    tratamento.xustificacions = [TratamentoXustificacion(codigo=c) for c in datos.xustificacions]
    tratamento.produtos = [TratamentoProduto(**vars(p)) for p in datos.produtos]
    tratamento.medidas = [TratamentoMedida(**vars(m)) for m in datos.medidas]
    tratamento.aplicadores = [TratamentoAplicador(**vars(a)) for a in datos.aplicadores]
    tratamento.asesor = TratamentoAsesor(**vars(datos.asesor)) if datos.asesor else None


def crear_tratamento_fito(
    session: Session, actor: Usuario, horta_id: int, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    tratamento = TratamentoFito(horta_id=horta_id, data_inicio=datos.data_inicio,
                                data_fin=datos.data_fin)
    _aplicar(tratamento, datos)
    session.add(tratamento)
    session.commit()
    return tratamento


def actualizar_tratamento_fito(
    session: Session, actor: Usuario, tratamento: TratamentoFito, datos: DatosTratamento
) -> TratamentoFito:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    horta = session.get(Horta, tratamento.horta_id)
    assert horta is not None
    _validar(session, horta, datos)
    _aplicar(tratamento, datos)
    session.commit()
    return tratamento


def dar_de_baixa_tratamento_fito(
    session: Session, actor: Usuario, tratamento: TratamentoFito
) -> None:
    comprobar_rol_horta(session, tratamento.horta_id, actor, _ROLES_ESCRITURA)
    tratamento.baixa = True
    session.commit()


def listar_tratamentos_fito(
    session: Session, actor: Usuario, horta_id: int
) -> list[TratamentoFito]:
    comprobar_rol_horta(session, horta_id, actor, _ROLES_LECTURA)
    return list(
        session.query(TratamentoFito)
        .filter_by(horta_id=horta_id, baixa=False)
        .order_by(TratamentoFito.data_inicio.desc(), TratamentoFito.id.desc())
        .all()
    )


def faltas_para_cue(tratamento: TratamentoFito) -> list[str]:
    """O que lle falta a un tratamento (p.ex. migrado ou de autoconsumo) para o CUE."""
    faltas = []
    if not tratamento.problemas:
        faltas.append("problema fitosanitario codificado")
    if not tratamento.xustificacions:
        faltas.append("xustificación")
    if not tratamento.produtos and not tratamento.medidas:
        faltas.append("produto ou medida codificados")
    if not tratamento.aplicadores:
        faltas.append("aplicador")
    if tratamento.eficacia is None:
        faltas.append("eficacia")
    return faltas
```

- [ ] **Step 4: Bloquear o borrado de cultivos/parcelas con tratamentos CUE**

En `src/horta/services/cultivos.py`, dentro de `eliminar_cultivo`, xusto despois de `comprobar_rol_horta(...)`:

```python
    if session.query(TratamentoCultivo).filter_by(cultivo_id=cultivo.id).first():
        raise OperacionNonPermitidaError(
            "Este cultivo ten tratamentos fitosanitarios rexistrados e debe conservarse "
            "(obriga legal). Podes marcalo como rematado."
        )
```
co import `from horta.models.tratamento_fito import TratamentoCultivo`.

En `src/horta/services/parcelas.py`, dentro de `eliminar_parcela`, despois de `comprobar_rol_horta(...)`:

```python
    ids_cultivos = [c.id for c in session.query(Cultivo).filter_by(parcela_id=parcela.id)]
    if ids_cultivos and session.query(TratamentoCultivo).filter(
        TratamentoCultivo.cultivo_id.in_(ids_cultivos)
    ).first():
        raise OperacionNonPermitidaError(
            "Esta parcela ten tratamentos fitosanitarios rexistrados e debe conservarse "
            "(obriga legal)."
        )
```
co import `from horta.models.tratamento_fito import TratamentoCultivo` (`OperacionNonPermitidaError` xa está importado).

Engadir a `tests/services/test_parcelas.py` un test equivalente a `test_non_se_pode_eliminar_cultivo_con_tratamentos` para `eliminar_parcela` (mesmo escenario, `match="tratamentos fitosanitarios"`).

- [ ] **Step 5: Executar todos os tests**

Run: `uv run pytest -q`
Expected: todos en verde (os tests antigos de `eliminar_cultivo` seguen pasando porque usan a táboa antiga `tratamento`).

- [ ] **Step 6: Commit**

```bash
git add src/horta/services/tratamentos_fito.py src/horta/services/cultivos.py src/horta/services/parcelas.py tests/services
git commit -m "feat: servizo de tratamentos fitosanitarios conforme ao CUE"
```

---

### Task 8: Comando `horta-catalogos` e procedemento de descarga (Claude)

**Files:**
- Create: `src/horta/cli_catalogos.py`
- Modify: `pyproject.toml` (`[project.scripts]`)
- Create: `docs/referencia/siex/descarga-catalogos.md`
- Test: `tests/test_cli_catalogos.py`

**Interfaces:**
- Consumes: `importar_catalogo`, `importar_cultivos`, `importar_variedades`, `CATALOGOS_XERAIS`, `cargar_nomes_galegos`.
- Produces: `main(argv: list[str] | None = None) -> int`; subcomandos `importar DIRECTORIO` e `nomes-galegos [CSV]`.

- [ ] **Step 1: Test que falla**

```python
# tests/test_cli_catalogos.py
from openpyxl import Workbook

from horta import cli_catalogos


def _xlsx(ruta, cab, filas):
    wb = Workbook()
    ws = wb.active
    ws.append(cab)
    for f in filas:
        ws.append(f)
    wb.save(ruta)


def test_importar_directorio(tmp_path, monkeypatch, session, capsys):
    monkeypatch.setattr(cli_catalogos, "get_session", lambda: _ContextoSesion(session))
    _xlsx(tmp_path / "PRODUCTOS.xlsx",
          ["Código", "Cultivo", "Latín", "EPPO", "C. UPOV", "Hortícola", "Integrado",
           "Fecha de alta", "Fecha de modificación", "Fecha de baja"],
          [["99", "PATATA", "", "SOLTU", "", "SI", "SI", None, None, None]])
    _xlsx(tmp_path / "UNIDADES_MEDIDA.xlsx",
          ["Código SIEX", "Unidades de medida", "Fecha de alta", "Fecha de modificación",
           "Fecha de baja"], [["1", "m2", None, None, None]])
    assert cli_catalogos.main(["importar", str(tmp_path)]) == 0
    saida = capsys.readouterr().out
    assert "cultivo: 1 altas" in saida
    assert "unidade_medida: 1 altas" in saida


class _ContextoSesion:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, *args):
        return False
```

- [ ] **Step 2: Executar e ver que falla**

Run: `uv run pytest tests/test_cli_catalogos.py -v`
Expected: FAIL con `ImportError`

- [ ] **Step 3: Implementar**

```python
# src/horta/cli_catalogos.py
"""horta-catalogos: importa os catálogos oficiais do FEGA descargados do portal SIEX."""

from __future__ import annotations

import argparse
from pathlib import Path

from horta.db import get_session
from horta.services.catalogos import cargar_nomes_galegos
from horta.services.catalogos_importar import (
    CATALOGOS_XERAIS,
    InformeImportacion,
    importar_catalogo,
    importar_cultivos,
    importar_variedades,
)

_NOMES_GALEGOS = Path(__file__).parent / "data" / "nomes_galegos.csv"


def _imprimir(informe: InformeImportacion) -> None:
    if informe.xa_importado:
        print(f"{informe.catalogo}: xa importado (sen cambios)")
    else:
        print(f"{informe.catalogo}: {informe.altas} altas, {informe.baixas} baixas, "
              f"{informe.cambios} cambios")


def _importar(directorio: Path) -> int:
    with get_session() as session:
        cultivos = directorio / "PRODUCTOS.xlsx"
        if cultivos.exists():
            _imprimir(importar_cultivos(session, cultivos))
        variedades = directorio / "VARIEDAD_ESPECIE_TIPO.xlsx"
        if variedades.exists():
            _imprimir(importar_variedades(session, variedades))
        for clave, (ficheiro, _, _) in CATALOGOS_XERAIS.items():
            ruta = directorio / f"{ficheiro}.xlsx"
            if ruta.exists():
                _imprimir(importar_catalogo(session, clave, ruta))
            else:
                print(f"{clave}: falta {ruta.name}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="horta-catalogos")
    sub = parser.add_subparsers(dest="orde", required=True)
    p_imp = sub.add_parser("importar", help="importa os XLSX dun directorio")
    p_imp.add_argument("directorio", type=Path)
    p_nom = sub.add_parser("nomes-galegos", help="carga os nomes galegos dos cultivos")
    p_nom.add_argument("csv", type=Path, nargs="?", default=_NOMES_GALEGOS)
    args = parser.parse_args(argv)
    if args.orde == "importar":
        return _importar(args.directorio)
    with get_session() as session:
        print(f"nomes galegos cargados: {cargar_nomes_galegos(session, args.csv)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

En `pyproject.toml`, `[project.scripts]`:
```toml
horta-catalogos = "horta.cli_catalogos:main"
```
Run: `uv sync`

- [ ] **Step 4: Procedemento documentado**

`docs/referencia/siex/descarga-catalogos.md`:

```markdown
# Descarga mensual dos catálogos do FEGA

Os catálogos actualízanse maioritariamente o día 1 de cada mes (índice METACATALOGO, campo cronExpre).

1. Abrir https://www3.sede.fega.gob.es/bdcsixpor/catalogos nun navegador normal.
2. Para cada catálogo da táboa de `CATALOGOS_XERAIS` (src/horta/services/catalogos_importar.py),
   máis "Cultivo" (PRODUCTOS) e "Variedad / Especie / Tipo" (VARIEDAD_ESPECIE_TIPO):
   filtrar polo nome, abrir o detalle e premer a icona de Excel.
3. Gardar cada ficheiro como `<CODIGO>.xlsx` (p.ex. `PLAGAS.xlsx`) nun directorio.
4. `uv run horta-catalogos importar <directorio>` e revisar o informe (altas, baixas, cambios).
5. Se hai baixas que afecten a tratamentos en curso, avisar ás persoas usuarias.

Non automatizar contra o servidor saltando o reCAPTCHA. Vía estable pendente: petición ao FEGA
(cau-fega@fega.es) ao abeiro da Lei 37/2007 de reutilización.
```

- [ ] **Step 5: Executar test e probar co material real**

Run: `uv run pytest tests/test_cli_catalogos.py -v` → 1 passed
Run: `cp horta.db /tmp/horta-proba.db && HORTA_DATABASE_URL=sqlite:////tmp/horta-proba.db uv run alembic upgrade head && HORTA_DATABASE_URL=sqlite:////tmp/horta-proba.db uv run horta-catalogos importar ../.playwright-mcp/fega && HORTA_DATABASE_URL=sqlite:////tmp/horta-proba.db uv run horta-catalogos nomes-galegos`
Expected: informe con ~1.121 cultivos, ~89.000 variedades e os catálogos xerais; segunda execución "xa importado".

- [ ] **Step 6: Commit**

```bash
git add src/horta/cli_catalogos.py pyproject.toml uv.lock docs/referencia/siex/descarga-catalogos.md tests/test_cli_catalogos.py
git commit -m "feat: comando horta-catalogos e procedemento de descarga"
```

---

### Task 9: UI de persoas e maquinaria (Claude; partes repetitivas para smoth)

**Files:**
- Create: `src/horta/ui/numeros.py`, `src/horta/ui/pages/persoas.py`, `src/horta/ui/pages/maquinaria.py`
- Modify: `src/horta/ui/pages/horta_detalle.py` (só engadir dúas pestanas)
- Test: `tests/ui/test_numeros.py`

**Interfaces:**
- Produces: `parsear_decimal(texto: str | float | None) -> float | None`; `seccion_persoas(horta_id: int, pode_editar: bool) -> None`; `seccion_maquinaria(horta_id: int, pode_editar: bool) -> None`.

- [ ] **Step 1: Test que falla**

```python
# tests/ui/test_numeros.py
import pytest

from horta.ui.numeros import parsear_decimal


@pytest.mark.parametrize("entrada,esperado", [
    ("1,5", 1.5), ("1.5", 1.5), (" 2 ", 2.0), ("", None), (None, None), (3, 3.0),
])
def test_parsear_decimal(entrada, esperado):
    assert parsear_decimal(entrada) == esperado


def test_parsear_decimal_invalido():
    with pytest.raises(ValueError, match="non é un número"):
        parsear_decimal("abc")
```

- [ ] **Step 2: Implementar `parsear_decimal`**

```python
# src/horta/ui/numeros.py
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
```

Run: `uv run pytest tests/ui/test_numeros.py -v` → 7 passed

- [ ] **Step 3: Sección de persoas**

```python
# src/horta/ui/pages/persoas.py
from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.models.persoa import Persoa, TipoCarne
from horta.services.persoas import actualizar_persoa, crear_persoa, listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.sesion import pechar_sesion, usuario_actual

_AVISO_DIAS = 30


def _data(texto: str | None) -> date | None:
    return date.fromisoformat(texto) if texto else None


def seccion_persoas(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        persoas = listar_persoas(session, actor, horta_id, so_activas=False)

    hoxe = date.today()
    for p in persoas:
        if p.activa and p.e_aplicador and p.ropo_caducidade:
            dias = (p.ropo_caducidade - hoxe).days
            if dias < 0:
                ui.label(f"⚠ O carné ROPO de {p.nome} caducou o {p.ropo_caducidade:%d/%m/%Y}") \
                    .classes("text-negative")
            elif dias <= _AVISO_DIAS:
                ui.label(f"⚠ O carné ROPO de {p.nome} caduca en {dias} días").classes("text-warning")

    filas = [
        {"id": p.id, "nome": f"{p.nome} {p.apelidos or ''}".strip(), "nif": p.nif or "",
         "funcion": ", ".join(x for x, s in (("aplicador", p.e_aplicador),
                                              ("asesor", p.e_asesor)) if s),
         "ropo": p.ropo_numero or "",
         "caducidade": f"{p.ropo_caducidade:%d/%m/%Y}" if p.ropo_caducidade else "",
         "activa": "si" if p.activa else "non"}
        for p in persoas
    ]
    ui.table(
        columns=[{"name": k, "label": l, "field": k} for k, l in (
            ("nome", "Nome"), ("nif", "NIF"), ("funcion", "Función"), ("ropo", "Nº ROPO"),
            ("caducidade", "Caducidade ROPO"), ("activa", "Activa"))],
        rows=filas, row_key="id",
    ).classes("w-full")

    if not pode_editar:
        return

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        ui.label("Nova persoa").classes("text-h6")
        nome = ui.input("Nome")
        apelidos = ui.input("Apelidos")
        nif = ui.input("NIF")
        aplicador = ui.checkbox("Aplicador de fitosanitarios")
        asesor = ui.checkbox("Asesor")
        ropo = ui.input("Nº ROPO")
        tipo = ui.select({t.value: t.value.replace("_", " ") for t in TipoCarne},
                         label="Tipo de carné")
        caducidade = ui.input("Caducidade do carné (AAAA-MM-DD)")
        regfer = ui.input("Nº REGFER")

        def gardar() -> None:
            if not nome.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: crear_persoa(
                    session, actor, horta_id, nome.value, apelidos=apelidos.value or None,
                    nif=nif.value or None, e_aplicador=aplicador.value, e_asesor=asesor.value,
                    ropo_numero=ropo.value or None,
                    ropo_tipo_carne=TipoCarne(tipo.value) if tipo.value else None,
                    ropo_caducidade=_data(caducidade.value), regfer_numero=regfer.value or None))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    ui.button("Nova persoa", icon="person_add", on_click=dialogo.open)


def desactivar_persoa(persoa_id: int) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        persoa = session.get(Persoa, persoa_id)
        if actor is None or persoa is None:
            return
        if executar_accion(session, lambda: actualizar_persoa(session, actor, persoa,
                                                              activa=False)):
            ui.navigate.reload()
```

- [ ] **Step 4: Sección de maquinaria** (mesma estrutura; smoth pode facela como tarefa literal copiando este bloque)

```python
# src/horta/ui/pages/maquinaria.py
from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.maquinaria import crear_maquina, listar_maquinas
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual


def seccion_maquinaria(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        maquinas = listar_maquinas(session, actor, horta_id, so_activas=False)

    filas = [
        {"id": m.id, "alias": m.alias, "marca": m.marca_modelo or "",
         "ident": m.num_roma or m.num_reganip or m.id_equipo_non_inscribible or "",
         "inspeccion": f"{m.data_ultima_inspeccion:%d/%m/%Y}" if m.data_ultima_inspeccion else "",
         "propia": "si" if m.propia else "non"}
        for m in maquinas
    ]
    ui.table(
        columns=[{"name": k, "label": l, "field": k} for k, l in (
            ("alias", "Nome"), ("marca", "Marca e modelo"), ("ident", "ROMA / REGANIP / ID"),
            ("inspeccion", "Última inspección"), ("propia", "Propia"))],
        rows=filas, row_key="id",
    ).classes("w-full")

    if not pode_editar:
        return

    with ui.dialog() as dialogo, ui.card().classes("w-96"):
        ui.label("Nova máquina").classes("text-h6")
        alias = ui.input("Nome")
        marca = ui.input("Marca e modelo")
        tipo_id = ui.select({"roma": "Nº ROMA", "reganip": "Nº REGANIP",
                             "outro": "Equipo non inscribible"}, value="roma",
                            label="Identificador")
        ident = ui.input("Número / identificador")
        propia = ui.checkbox("Propia", value=True)
        potencia = ui.input("Potencia")
        inspeccion = ui.input("Data última inspección (AAAA-MM-DD)")

        def gardar() -> None:
            if not alias.value:
                ui.notify("O nome é obrigatorio", type="negative")
                return
            campo = {"roma": "num_roma", "reganip": "num_reganip",
                     "outro": "id_equipo_non_inscribible"}[tipo_id.value]
            with get_session() as session:
                actor = usuario_actual(session)
                if actor is None:
                    pechar_sesion()
                    return
                ok = executar_accion(session, lambda: crear_maquina(
                    session, actor, horta_id, alias.value, marca_modelo=marca.value or None,
                    propia=propia.value, potencia=parsear_decimal(potencia.value),
                    data_ultima_inspeccion=date.fromisoformat(inspeccion.value)
                    if inspeccion.value else None,
                    **({campo: ident.value} if ident.value else {})))
            if ok:
                ui.navigate.reload()

        with ui.row():
            ui.button("Gardar", icon="check", on_click=gardar)
            ui.button("Cancelar", on_click=dialogo.close).props("flat")

    ui.button("Nova máquina", icon="agriculture", on_click=dialogo.open)
```

- [ ] **Step 5: Enlazar as pestanas en `horta_detalle.py`**

Antes:
```python
        pestana_animais = ui.tab("Animais")
```
Despois:
```python
        pestana_animais = ui.tab("Animais")
        pestana_persoas = ui.tab("Persoas")
        pestana_maquinaria = ui.tab("Maquinaria")
```

Antes:
```python
        with ui.tab_panel(pestana_animais):
```
Despois (manter a liña seguinte orixinal debaixo):
```python
        with ui.tab_panel(pestana_persoas):
            seccion_persoas(horta_id, pode_editar)
        with ui.tab_panel(pestana_maquinaria):
            seccion_maquinaria(horta_id, pode_editar)
        with ui.tab_panel(pestana_animais):
```
e os imports `from horta.ui.pages.persoas import seccion_persoas` e `from horta.ui.pages.maquinaria import seccion_maquinaria`.

- [ ] **Step 6: Comprobar e probar no navegador**

Run: `uv run ruff check src tests && uv run mypy src && uv run pytest -q`
Probar con `uv run horta`: crear un aplicador con carné caducado → aviso vermello; crear máquina con ROMA e REGANIP a vez → non é posible (só un campo).

- [ ] **Step 7: Commit**

```bash
git add src/horta/ui tests/ui/test_numeros.py
git commit -m "feat: pestanas de persoas e maquinaria"
```

---

### Task 10: UI do tratamento fitosanitario en 5 pasos (Claude)

**Files:**
- Create: `src/horta/ui/pages/tratamentos_fito.py`
- Modify: `src/horta/ui/pages/horta_detalle.py` (substituír o panel de tratamentos e eliminar `_seccion_tratamentos`)

**Interfaces:**
- Consumes: `buscar_cultivos`, `valores_vixentes`, `describir`, servizos da Tarefa 7, `listar_persoas`, `listar_maquinas`, `parsear_decimal`.
- Produces: `seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None`.

- [ ] **Step 1: Implementar a sección**

```python
# src/horta/ui/pages/tratamentos_fito.py
from __future__ import annotations

from datetime import date, time

from nicegui import ui

from horta.db import get_session
from horta.models.cultivo import Cultivo
from horta.models.parcela import Parcela
from horta.models.tratamento_fito import TIPOS_PROBLEMA
from horta.services.catalogos import describir, valores_vixentes
from horta.services.cultivos import listar_cultivos
from horta.services.maquinaria import listar_maquinas
from horta.services.persoas import listar_persoas
from horta.services.tratamentos_fito import (
    DatosTratamento,
    LinhaAplicador,
    LinhaCultivo,
    LinhaProduto,
    Problema,
    crear_tratamento_fito,
    faltas_para_cue,
    listar_tratamentos_fito,
)
from horta.ui.accions import executar_accion
from horta.ui.numeros import parsear_decimal
from horta.ui.sesion import pechar_sesion, usuario_actual

_ETIQUETA_PROBLEMA = {"enfermidade": "Enfermidade", "praga": "Praga (artrópodos/gasterópodos)",
                      "mala_herba": "Mala herba", "regulador": "Regulador / outros"}


def _opcions(session, catalogo: str) -> dict[str, str]:
    return {v.codigo: v.descricion for v in valores_vixentes(session, catalogo)}


def seccion_tratamentos_fito(horta_id: int, pode_editar: bool) -> None:
    with get_session() as session:
        actor = usuario_actual(session)
        if actor is None:
            pechar_sesion()
            return
        tratamentos = listar_tratamentos_fito(session, actor, horta_id)
        filas = []
        for t in tratamentos:
            cultivos = [session.get(Cultivo, c.cultivo_id) for c in t.cultivos]
            filas.append({
                "id": t.id,
                "data": f"{t.data_inicio:%d/%m/%Y}",
                "cultivos": ", ".join(c.especie for c in cultivos if c),
                "problemas": ", ".join(describir(session, p.tipo, p.codigo) for p in t.problemas)
                or (t.observacions or ""),
                "produtos": ", ".join(p.nome_comercial or p.num_rexistro or "" for p in t.produtos)
                or (t.orixinal_produto or ""),
                "cue": "completo" if not faltas_para_cue(t)
                else "falta: " + ", ".join(faltas_para_cue(t)),
            })
        cultivos_horta = listar_cultivos(session, actor, horta_id)
        parcelas = {p.id: p for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        opcions_cultivo = {c.id: f"{c.especie} {c.variedade or ''} — "
                                 f"{parcelas[c.parcela_id].nome}".strip()
                           for c in cultivos_horta}
        problemas = {tipo: _opcions(session, tipo) for tipo in TIPOS_PROBLEMA}
        xustificacions = _opcions(session, "xustificacion")
        estados = _opcions(session, "estado_fenoloxico")
        unidades = _opcions(session, "unidade_medida")
        tipos_produto = _opcions(session, "tipo_produto")
        eficacias = _opcions(session, "eficacia")
        aplicadores = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)
                       if p.e_aplicador}
        maquinas = {m.id: m.alias for m in listar_maquinas(session, actor, horta_id)}

    ui.table(
        columns=[{"name": k, "label": l, "field": k} for k, l in (
            ("data", "Data"), ("cultivos", "Cultivos"), ("problemas", "Problema"),
            ("produtos", "Produtos"), ("cue", "CUE"))],
        rows=filas, row_key="id",
    ).classes("w-full")

    if not pode_editar:
        return
    if not problemas["enfermidade"]:
        ui.label("Faltan os catálogos oficiais. Un administrador debe executar "
                 "`horta-catalogos importar`.").classes("text-negative")
        return

    with ui.dialog() as dialogo, ui.card().classes("w-[40rem]"):
        with ui.stepper().props("vertical").classes("w-full") as pasos:
            with ui.step("1. Que e onde"):
                data_inicio = ui.input("Data de inicio (AAAA-MM-DD)",
                                       value=date.today().isoformat())
                data_fin = ui.input("Data de fin (AAAA-MM-DD)", value=date.today().isoformat())
                hora = ui.input("Hora de inicio (HH:MM, opcional)")
                cultivo = ui.select(opcions_cultivo, label="Cultivo e parcela",
                                    with_input=True)
                superficie = ui.input("Superficie tratada (ha)")
                estado = ui.select(estados, label="Estado fenolóxico")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
            with ui.step("2. Por que"):
                tipo_problema = ui.select(_ETIQUETA_PROBLEMA, value="enfermidade",
                                          label="Tipo de problema")
                problema = ui.select(problemas["enfermidade"], label="Problema",
                                     with_input=True)
                tipo_problema.on_value_change(
                    lambda e: problema.set_options(problemas[e.value], value=None))
                xustificacion = ui.select(xustificacions, label="Xustificación")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("3. Con que"):
                tipo_produto = ui.select(tipos_produto, value=next(iter(tipos_produto), None),
                                         label="Tipo de produto")
                nome_comercial = ui.input("Nome comercial")
                num_rexistro = ui.input("Nº de rexistro")
                materia_activa = ui.input("Materia activa")
                dose = ui.input("Dose (por hectárea)")
                unidade = ui.select(unidades, label="Unidade", with_input=True)
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("4. Quen"):
                aplicador = ui.select(aplicadores, label="Aplicador")
                maquina = ui.select(maquinas, label="Máquina (baleiro se é manual)")
                with ui.stepper_navigation():
                    ui.button("Seguinte", on_click=pasos.next)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
            with ui.step("5. Resultado"):
                eficacia = ui.select(eficacias, label="Eficacia")
                observacions = ui.textarea("Observacións")

                def gardar() -> None:
                    if cultivo.value is None or problema.value is None:
                        ui.notify("Indica o cultivo e o problema", type="negative")
                        return
                    with get_session() as session:
                        actor_actual = usuario_actual(session)
                        if actor_actual is None:
                            pechar_sesion()
                            return

                        def crear() -> None:
                            datos = DatosTratamento(
                                data_inicio=date.fromisoformat(data_inicio.value),
                                data_fin=date.fromisoformat(data_fin.value),
                                hora=time.fromisoformat(hora.value) if hora.value else None,
                                cultivos=[LinhaCultivo(cultivo.value,
                                                       parsear_decimal(superficie.value),
                                                       estado.value)],
                                problemas=[Problema(tipo_problema.value, problema.value)],
                                xustificacions=[xustificacion.value] if xustificacion.value
                                else [],
                                produtos=[LinhaProduto(
                                    tipo_produto=tipo_produto.value, unidade=unidade.value,
                                    num_rexistro=num_rexistro.value or None,
                                    nome_comercial=nome_comercial.value or None,
                                    materia_activa=materia_activa.value or None,
                                    dose=parsear_decimal(dose.value))],
                                aplicadores=[LinhaAplicador(aplicador.value, maquina.value,
                                                            aplicacion_manual=maquina.value
                                                            is None)]
                                if aplicador.value else [],
                                eficacia=eficacia.value,
                                observacions=observacions.value or None,
                            )
                            crear_tratamento_fito(session, actor_actual, horta_id, datos)

                        ok = executar_accion(session, crear)
                    if ok:
                        ui.navigate.reload()

                with ui.stepper_navigation():
                    ui.button("Gardar", icon="check", on_click=gardar)
                    ui.button("Atrás", on_click=pasos.previous).props("flat")
        ui.button("Pechar", on_click=dialogo.close).props("flat")

    ui.button("Novo tratamento", icon="add", on_click=dialogo.open)
```

Nota: este primeiro formulario rexistra **un** cultivo, **un** problema e **un** produto (o caso máis común). O servizo xa admite varios; engadir filas múltiples na UI é unha tarefa posterior separada (non bloquea o cumprimento: varios tratamentos simples son igualmente válidos).

`date.fromisoformat` con texto mal escrito lanza `ValueError`, que `executar_accion` amosa como "erro inesperado". Para dar unha mensaxe clara, envolver as conversións de data e hora nunha función `_data(texto)` que lance `OperacionNonPermitidaError("Data non válida: usa AAAA-MM-DD")`:

```python
def _data(texto: str) -> date:
    try:
        return date.fromisoformat(texto.strip())
    except ValueError:
        raise OperacionNonPermitidaError("Data non válida: usa AAAA-MM-DD") from None
```
(con `from horta.services.errors import OperacionNonPermitidaError`) e usala en `data_inicio`/`data_fin`.

- [ ] **Step 2: Substituír o panel en `horta_detalle.py`**

Antes:
```python
        with ui.tab_panel(pestana_tratamentos):
            _seccion_tratamentos(horta_id, tratamentos, cultivos, parcelas, pode_editar)
```
Despois:
```python
        with ui.tab_panel(pestana_tratamentos):
            seccion_tratamentos_fito(horta_id, pode_editar)
```
Engadir `from horta.ui.pages.tratamentos_fito import seccion_tratamentos_fito`. Borrar a función `_seccion_tratamentos` e as consultas/imports que deixen de usarse (ruff indicaraos). Os servizos antigos `tratamentos.py` e os seus tests quedan ata unha limpeza posterior (a táboa antiga conserva os datos orixinais).

- [ ] **Step 3: Comprobacións e proba manual**

Run: `uv run ruff check src tests && uv run mypy src && uv run pytest -q` → verde.
Con `uv run horta` e unha BD con catálogos importados (Tarefa 8):
1. Rexistrar un tratamento completo → aparece na lista con "CUE: completo".
2. Aplicador co carné caducado na data → mensaxe "O carné ROPO de X caducou…".
3. Dose "1,5" → gárdase 1.5.
4. Data "32/13/2026" → "Data non válida".
5. Os tratamentos migrados aparecen con "falta: …".

- [ ] **Step 4: Commit**

```bash
git add src/horta/ui
git commit -m "feat: formulario de tratamento fitosanitario CUE en 5 pasos"
```

---

### Task 11: Peche da fase (Claude)

- [ ] **Step 0:** Anotar en `docs/estado-e-evolucion.md` como pendentes: aviso de inspección de maquinaria vencida (periodicidade legal por confirmar, spec §11.2), carga de variedades locais galegas (táboa `variedade_local` sen datos aínda), selector de cultivo oficial no formulario de cultivos, UI con varias filas por tratamento.
- [ ] **Step 1:** Actualizar `CLAUDE.md` (sección Arquitectura: novos modelos, servizos e comando `horta-catalogos`) e `docs/estado-e-evolucion.md` (fase 1 feita, pendentes: UI multi-fila, limpeza do modelo antigo, petición ao FEGA).
- [ ] **Step 2:** Revisión completa da rama (`/code-review` ou revisor) e corrección do que saia.
- [ ] **Step 3:** Commit `docs: peche da fase 1 do caderno de tratamentos`.

---

## Reparto Claude / smoth

| Tarefa | Quen | Como |
|---|---|---|
| 1, 2, 3, 6, 6b, 7, 8, 10, 11 | Claude | directamente |
| 4, 5 | smoth | tarefa literal: "crea o ficheiro X co contido Y" + tests, a partir do código desta folla, con proba en seco previa |
| 9 (maquinaria.py) | smoth | idem, despois de que Claude faga `numeros.py` e `persoas.py` |
| Nomes galegos (CSV, Tarefa 3 step 4–5) | smoth | engadir liñas a partir da saída do script |
