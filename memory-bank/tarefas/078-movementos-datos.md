# Tarefa 078 — Entradas e saídas de animais (1/11 datos): táboa de movementos e especie oficial

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos hai unha táboa para as entradas e saídas de cada grupo de animais e o grupo garda o código oficial da especie; os grupos que xa hai reciben o seu movemento inicial. Deseño: `docs/superpowers/specs/2026-10-28-entradas-saidas-animais-design.md`

## Ficheiros a tocar

- `alembic/versions/a4b6d8f0c2e5_movemento_animal.py` (**ficheiro novo**)
- `src/horta/models/movemento_animal.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `src/horta/models/animal.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/a4b6d8f0c2e5_movemento_animal.py`

Contido completo:
```python
"""entradas e saídas de animais; especie do catálogo oficial

Revision ID: a4b6d8f0c2e5
Revises: f3a5c7e9b1d4
Create Date: 2026-10-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4b6d8f0c2e5'
down_revision: Union[str, Sequence[str], None] = 'f3a5c7e9b1d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "movemento_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("cantidade", sa.Integer(), nullable=False),
        sa.Column("identificacion", sa.String(length=500), nullable=True),
        sa.Column("titular", sa.String(length=300), nullable=True),
        sa.Column("rega", sa.String(length=20), nullable=True),
        sa.Column("codigo_movemento", sa.String(length=50), nullable=True),
        sa.Column("causa", sa.String(length=300), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_movemento_animal_horta_id", "movemento_animal", ["horta_id"])
    op.create_index("ix_movemento_animal_animal_id", "movemento_animal", ["animal_id"])
    with op.batch_alter_table("animal") as batch:
        batch.add_column(sa.Column("especie_codigo", sa.String(length=20), nullable=True))
    # Os grupos que xa existen: os seus animais entran como movemento inicial na data de alta
    op.execute(
        "INSERT INTO movemento_animal (horta_id, animal_id, data, tipo, cantidade, baixa, "
        "created_at) SELECT horta_id, id, data_alta, 'inicial', cantidade, 0, CURRENT_TIMESTAMP "
        "FROM animal WHERE cantidade > 0"
    )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("animal") as batch:
        batch.drop_column("especie_codigo")
    op.drop_index("ix_movemento_animal_animal_id", table_name="movemento_animal")
    op.drop_index("ix_movemento_animal_horta_id", table_name="movemento_animal")
    op.drop_table("movemento_animal")
```

### Paso 2 — crear o ficheiro `src/horta/models/movemento_animal.py`

Contido completo:
```python
"""Entradas e saídas de animais de cada grupo (libro de rexistro gandeiro, RD 787/2023 anexo
V 9 e 10). A cantidade do grupo é a suma dos seus movementos. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class MovementoAnimal(Base):
    __tablename__ = "movemento_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    # services.movementos_animais.TIPOS_MOVEMENTO
    tipo: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[int] = mapped_column(Integer)
    identificacion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Entrada: o titular anterior e a explotación de orixe; saída: o novo e a de destino
    titular: Mapped[str | None] = mapped_column(String(300), default=None)
    rega: Mapped[str | None] = mapped_column(String(20), default=None)
    codigo_movemento: Mapped[str | None] = mapped_column(String(50), default=None)
    # Morte ou sacrificio
    causa: Mapped[str | None] = mapped_column(String(300), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.maquina import Maquina
```

Despois:
```python
from horta.models.maquina import Maquina
from horta.models.movemento_animal import MovementoAnimal
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "CoidadoAnimal",
```

Despois:
```python
    "CoidadoAnimal",
    "MovementoAnimal",
```

### Paso 5 — `src/horta/models/animal.py`

Antes:
```python
    especie: Mapped[str] = mapped_column(String(80))
    raza: Mapped[str | None] = mapped_column(String(120), default=None)
```

Despois:
```python
    # Nome do grupo (p.ex. «Galiñas do galiñeiro de abaixo») e a especie no catálogo oficial
    especie: Mapped[str] = mapped_column(String(80))
    especie_codigo: Mapped[str | None] = mapped_column(String(20), default=None)
    raza: Mapped[str | None] = mapped_column(String(120), default=None)
    # Cantidade, data de baixa e estado saen dos movementos (services.movementos_animais)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Entradas e saídas de animais (1/11 datos): táboa de movementos e especie oficial: feito.
