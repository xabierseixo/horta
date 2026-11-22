# Tarefa 060c — Quitar os campos vellos do modelo do cultivo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 060b. **Axente**: qwen-66 (mantemento).

## Obxectivo

Paso 3 de 3: quitar os cinco campos do modelo e da táboa. A migración pasa antes as datas vellas a tipo_inicio/data_inicio/data_fin se estes están baleiros (proba incluída).

## Ficheiros a tocar

- `src/horta/models/cultivo.py`
- `alembic/versions/b1d3f5a7c9e2_quitar_campos_vellos_do_cultivo.py` (**ficheiro novo**)
- `tests/test_migracion_campos_cultivo.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/cultivo.py`

Antes:
```python
    )
    data_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    data_plantacion: Mapped[date | None] = mapped_column(Date, default=None)
```

Despois:
```python
    )
```

### Paso 2 — `src/horta/models/cultivo.py`

Antes:
```python
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
    data_colleita_real: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(30), default=None)
```

Despois:
```python
    data_colleita_prevista: Mapped[date | None] = mapped_column(Date, default=None)
```

### Paso 3 — crear o ficheiro `alembic/versions/b1d3f5a7c9e2_quitar_campos_vellos_do_cultivo.py`

Contido completo:
```python
"""quitar os campos vellos do cultivo (substituídos por data_inicio/data_fin e colleitas)

Revision ID: b1d3f5a7c9e2
Revises: d6f8b0c2e4a7
Create Date: 2026-10-25 04:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b1d3f5a7c9e2"
down_revision: Union[str, Sequence[str], None] = "d6f8b0c2e4a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Non perder datas: pásanse aos campos novos se estes están baleiros
    op.execute(
        "UPDATE cultivo SET "
        "tipo_inicio = COALESCE(tipo_inicio, CASE WHEN data_sementeira IS NOT NULL "
        "THEN 'sementeira' WHEN data_plantacion IS NOT NULL THEN 'plantacion' END), "
        "data_inicio = COALESCE(data_inicio, data_sementeira, data_plantacion), "
        "data_fin = COALESCE(data_fin, data_colleita_real)"
    )
    with op.batch_alter_table("cultivo") as taboa:
        for columna in ("data_sementeira", "data_plantacion", "data_colleita_real",
                        "cantidade", "unidade"):
            taboa.drop_column(columna)


def downgrade() -> None:
    with op.batch_alter_table("cultivo") as taboa:
        taboa.add_column(sa.Column("data_sementeira", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("data_plantacion", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("data_colleita_real", sa.Date(), nullable=True))
        taboa.add_column(sa.Column("cantidade", sa.Float(), nullable=True))
        taboa.add_column(sa.Column("unidade", sa.String(length=30), nullable=True))
```

### Paso 4 — crear o ficheiro `tests/test_migracion_campos_cultivo.py`

Contido completo:
```python
import os
import subprocess
import sys
from pathlib import Path

from sqlalchemy import create_engine, text

RAIZ = Path(__file__).resolve().parents[1]


def _alembic(url: str, *args: str) -> None:
    subprocess.run([sys.executable, "-m", "alembic", *args], cwd=RAIZ,
                   env={**os.environ, "HORTA_DATABASE_URL": url}, check=True,
                   capture_output=True)


def test_as_datas_vellas_pasan_aos_campos_novos(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "d6f8b0c2e4a7")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO horta (id, nome, uso_profesional, "
                          "asesoramento_fertilizacion, created_at) "
                          "VALUES (1, 'Horta', 1, 0, '2026-01-01')"))
        conn.execute(text("INSERT INTO parcela (id, horta_id, nome, estado, pequena_superficie, "
                          "created_at) VALUES (1, 1, 'P1', 'activa', 0, '2026-01-01')"))
        for fila in ("(1, 'Pataca', '2026-03-01', NULL, '2026-08-01', NULL, NULL)",
                     "(2, 'Leituga', NULL, '2026-04-01', NULL, NULL, NULL)",
                     "(3, 'Tomate', '2026-03-01', NULL, NULL, '2026-05-01', 'plantacion')"):
            conn.execute(text(
                "INSERT INTO cultivo (id, especie, data_sementeira, data_plantacion, "
                "data_colleita_real, data_inicio, tipo_inicio, parcela_id, estado, "
                "material_tratado, material_adquirido, sementeira_directa, "
                "producion_integrada, created_at) VALUES " + fila[:-1]
                + ", 1, 'planificado', 0, 0, 0, 0, '2026-01-01')"))
    _alembic(url, "upgrade", "b1d3f5a7c9e2")
    with engine.connect() as conn:
        filas = conn.execute(text("SELECT id, tipo_inicio, data_inicio, data_fin FROM cultivo "
                                  "ORDER BY id")).all()
    assert filas == [(1, "sementeira", "2026-03-01", "2026-08-01"),
                     (2, "plantacion", "2026-04-01", None),
                     (3, "plantacion", "2026-05-01", None)]  # os datos novos mandan
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

O cultivo xa non ten os campos vellos; as datas que houbese pasaron aos campos novos.
