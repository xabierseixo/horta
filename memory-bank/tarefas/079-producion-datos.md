# Tarefa 079 — Produción dos animais (1/11 datos): táboa da produción

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos hai unha táboa para a produción de cada grupo de animais (ovos, leite, mel...) co seu lote. Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `alembic/versions/b5d7f9a1c3e6_producion_animal.py` (**ficheiro novo**)
- `src/horta/models/producion_animal.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/b5d7f9a1c3e6_producion_animal.py`

Contido completo:
```python
"""produción dos animais

Revision ID: b5d7f9a1c3e6
Revises: a4b6d8f0c2e5
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5d7f9a1c3e6'
down_revision: Union[str, Sequence[str], None] = 'a4b6d8f0c2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "producion_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=False),
        sa.Column("produto", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(length=20), nullable=False),
        sa.Column("retirada", sa.Float(), nullable=True),
        sa.Column("lote", sa.String(length=40), nullable=False),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_producion_animal_horta_id", "producion_animal", ["horta_id"])
    op.create_index("ix_producion_animal_animal_id", "producion_animal", ["animal_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_producion_animal_animal_id", table_name="producion_animal")
    op.drop_index("ix_producion_animal_horta_id", table_name="producion_animal")
    op.drop_table("producion_animal")
```

### Paso 2 — crear o ficheiro `src/horta/models/producion_animal.py`

Contido completo:
```python
"""Produción de cada grupo de animais (ovos, leite, mel...), co seu lote, como as colleitas dos
cultivos (README §7). Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class ProducionAnimal(Base):
    __tablename__ = "producion_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # Un período (p.ex. os ovos da semana); igual á data se é un só día
    data_fin: Mapped[date] = mapped_column(Date)
    # services.producions_animais.PRODUTOS
    produto: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    # O que non vale: rotos, ou o que se tira polo tempo de espera dun medicamento
    retirada: Mapped[float | None] = mapped_column(Float, default=None)
    # Trazabilidade (Reg. CE 178/2002 art. 18): único na explotación, xunto cos das colleitas
    lote: Mapped[str] = mapped_column(String(40))
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.persoa import Persoa, TipoCarne
```

Despois:
```python
from horta.models.persoa import Persoa, TipoCarne
from horta.models.producion_animal import ProducionAnimal
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "MovementoAnimal",
```

Despois:
```python
    "MovementoAnimal",
    "ProducionAnimal",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (1/11 datos): táboa da produción: feito.
