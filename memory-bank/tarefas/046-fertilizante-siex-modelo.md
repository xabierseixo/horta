# Tarefa 046 — Modelo do catálogo oficial de abonos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O FEGA publica 1.243 produtos fertilizantes (DETALLE_MATERIAL_FERT) co material SIEX, nome comercial, fabricante e riqueza en N, P₂O₅ e K₂O. Gárdanse nunha táboa propia (`fertilizante_siex`), como `cultivo_siex`, para que ao apuntar un abonado se poida escoller o produto e encher a riqueza. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md`.

## Ficheiros a tocar

- `src/horta/models/fertilizante.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `alembic/versions/d8a1f3c5e7b9_fertilizante_siex.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/fertilizante.py`

Contido completo:
```python
"""Abonos: catálogo oficial de produtos fertilizantes do FEGA (DETALLE_MATERIAL_FERT)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class FertilizanteSiex(Base):
    """Produto fertilizante oficial: material SIEX, nome comercial, fabricante e riqueza."""

    __tablename__ = "fertilizante_siex"

    codigo: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    material: Mapped[str] = mapped_column(String(20), index=True)
    clase: Mapped[str | None] = mapped_column(String(60), default=None)
    subclase: Mapped[str | None] = mapped_column(String(60), default=None)
    nome: Mapped[str] = mapped_column(String(300))
    fabricante: Mapped[str | None] = mapped_column(String(200), default=None)
    n_pct: Mapped[float] = mapped_column(Float, default=0)
    p2o5_pct: Mapped[float] = mapped_column(Float, default=0)
    k2o_pct: Mapped[float] = mapped_column(Float, default=0)
    liquido: Mapped[bool] = mapped_column(Boolean, default=False)
    densidade: Mapped[float | None] = mapped_column(Float, default=None)
    inhibidor_nitrificacion: Mapped[bool] = mapped_column(Boolean, default=False)
    inhibidor_ureasa: Mapped[bool] = mapped_column(Boolean, default=False)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))
```

### Paso 2 — `src/horta/models/__init__.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
from horta.models.fertilizante import FertilizanteSiex
```

### Paso 3 — `src/horta/models/__init__.py`: engadir á lista

Antes:
```python
    "VariedadeSiex",
```

Despois:
```python
    "VariedadeSiex",
    "FertilizanteSiex",
```

### Paso 4 — crear o ficheiro `alembic/versions/d8a1f3c5e7b9_fertilizante_siex.py`

Contido completo:
```python
"""catálogo oficial de produtos fertilizantes (DETALLE_MATERIAL_FERT)

Revision ID: d8a1f3c5e7b9
Revises: c7f2a9d1e4b6
Create Date: 2026-10-25 10:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8a1f3c5e7b9"
down_revision: Union[str, Sequence[str], None] = "c7f2a9d1e4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fertilizante_siex",
        sa.Column("codigo", sa.Integer(), autoincrement=False, nullable=False),
        sa.Column("material", sa.String(length=20), nullable=False),
        sa.Column("clase", sa.String(length=60), nullable=True),
        sa.Column("subclase", sa.String(length=60), nullable=True),
        sa.Column("nome", sa.String(length=300), nullable=False),
        sa.Column("fabricante", sa.String(length=200), nullable=True),
        sa.Column("n_pct", sa.Float(), nullable=False),
        sa.Column("p2o5_pct", sa.Float(), nullable=False),
        sa.Column("k2o_pct", sa.Float(), nullable=False),
        sa.Column("liquido", sa.Boolean(), nullable=False),
        sa.Column("densidade", sa.Float(), nullable=True),
        sa.Column("inhibidor_nitrificacion", sa.Boolean(), nullable=False),
        sa.Column("inhibidor_ureasa", sa.Boolean(), nullable=False),
        sa.Column("data_baixa", sa.Date(), nullable=True),
        sa.Column("version_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["version_id"], ["catalogo_version.id"]),
        sa.PrimaryKeyConstraint("codigo"),
    )
    op.create_index("ix_fertilizante_siex_material", "fertilizante_siex", ["material"])


def downgrade() -> None:
    op.drop_index("ix_fertilizante_siex_material", table_name="fertilizante_siex")
    op.drop_table("fertilizante_siex")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existe a táboa `fertilizante_siex` co seu modelo.
