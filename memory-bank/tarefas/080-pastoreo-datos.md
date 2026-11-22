# Tarefa 080 — Pastoreo (1/11 datos): táboas do pastoreo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos hai táboas para o pastoreo: datas, leiras e animais (propios ou doutra persoa). Deseño: `docs/superpowers/specs/2026-10-28-pastoreo-design.md`

## Ficheiros a tocar

- `alembic/versions/c6e8a0b2d4f7_pastoreo.py` (**ficheiro novo**)
- `src/horta/models/pastoreo.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/c6e8a0b2d4f7_pastoreo.py`

Contido completo:
```python
"""pastoreo

Revision ID: c6e8a0b2d4f7
Revises: b5d7f9a1c3e6
Create Date: 2026-10-28 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6e8a0b2d4f7'
down_revision: Union[str, Sequence[str], None] = 'b5d7f9a1c3e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "pastoreo",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("uuid", sa.String(length=36), nullable=True),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("uuid"),
    )
    op.create_index("ix_pastoreo_horta_id", "pastoreo", ["horta_id"])
    op.create_table(
        "pastoreo_leira",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pastoreo_id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("superficie_ha", sa.Float(), nullable=True),
        sa.Column("tipo_cobertura", sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(["pastoreo_id"], ["pastoreo.id"]),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pastoreo_leira_pastoreo_id", "pastoreo_leira", ["pastoreo_id"])
    op.create_index("ix_pastoreo_leira_cultivo_id", "pastoreo_leira", ["cultivo_id"])
    op.create_table(
        "pastoreo_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("pastoreo_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=True),
        sa.Column("rega", sa.String(length=14), nullable=True),
        sa.Column("especie_codigo", sa.String(length=20), nullable=True),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["pastoreo_id"], ["pastoreo.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pastoreo_animal_pastoreo_id", "pastoreo_animal", ["pastoreo_id"])
    op.create_index("ix_pastoreo_animal_animal_id", "pastoreo_animal", ["animal_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_pastoreo_animal_animal_id", table_name="pastoreo_animal")
    op.drop_index("ix_pastoreo_animal_pastoreo_id", table_name="pastoreo_animal")
    op.drop_table("pastoreo_animal")
    op.drop_index("ix_pastoreo_leira_cultivo_id", table_name="pastoreo_leira")
    op.drop_index("ix_pastoreo_leira_pastoreo_id", table_name="pastoreo_leira")
    op.drop_table("pastoreo_leira")
    op.drop_index("ix_pastoreo_horta_id", table_name="pastoreo")
    op.drop_table("pastoreo")
```

### Paso 2 — crear o ficheiro `src/horta/models/pastoreo.py`

Contido completo:
```python
"""Pastoreo (CUE bloque 12): o gando nunha ou máis leiras entre dúas datas. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Pastoreo(Base):
    __tablename__ = "pastoreo"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    # Baleira mentres o gando segue no pasto
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
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

    leiras: Mapped[list[PastoreoLeira]] = relationship(cascade="all, delete-orphan")
    animais: Mapped[list[PastoreoAnimal]] = relationship(cascade="all, delete-orphan")


class PastoreoLeira(Base):
    __tablename__ = "pastoreo_leira"

    id: Mapped[int] = mapped_column(primary_key=True)
    pastoreo_id: Mapped[int] = mapped_column(ForeignKey("pastoreo.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    # Superficie pastada; baleira = a do cultivo
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    # Catálogo tipo_cobertura_solo
    tipo_cobertura: Mapped[str | None] = mapped_column(String(20), default=None)


class PastoreoAnimal(Base):
    __tablename__ = "pastoreo_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    pastoreo_id: Mapped[int] = mapped_column(ForeignKey("pastoreo.id"), index=True)
    # Animais propios: o grupo. De terceiros: sen grupo, co REGA e a especie
    animal_id: Mapped[int | None] = mapped_column(ForeignKey("animal.id"), index=True,
                                                  default=None)
    rega: Mapped[str | None] = mapped_column(String(14), default=None)
    # Catálogo especie_animal
    especie_codigo: Mapped[str | None] = mapped_column(String(20), default=None)
    numero: Mapped[int] = mapped_column(Integer)
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.parcela import Parcela, SecanoRegadio
```

Despois:
```python
from horta.models.parcela import Parcela, SecanoRegadio
from horta.models.pastoreo import Pastoreo, PastoreoAnimal, PastoreoLeira
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "ProducionAnimal",
```

Despois:
```python
    "ProducionAnimal",
    "Pastoreo",
    "PastoreoLeira",
    "PastoreoAnimal",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Pastoreo (1/11 datos): táboas do pastoreo: feito.
