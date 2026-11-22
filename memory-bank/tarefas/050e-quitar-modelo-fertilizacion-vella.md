# Tarefa 050e — Quitar o modelo e a táboa da fertilización vella

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 050d. **Axente**: qwen-66 (mantemento).

## Obxectivo

A fertilización vella (`Fertilizacion`, táboa `fertilizacion`) xa non a usa ningunha pantalla nin proba: a sección Fertilización usa os abonados novos. Paso 5: quitar a clase e borrar a táboa cunha migración (a volta atrás crea a táboa baleira).

## Ficheiros a tocar

- `src/horta/models/cultivo.py`
- `src/horta/models/__init__.py`
- `alembic/versions/f1e3a5c7b9d2_quitar_fertilizacion_vella.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/cultivo.py`: quitar a clase

Antes:
```python
    )


class Fertilizacion(Base):
    __tablename__ = "fertilizacion"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    superficie: Mapped[float | None] = mapped_column(Float, default=None)  # hectáreas
    tipo: Mapped[str] = mapped_column(String(50))
    produto: Mapped[str] = mapped_column(String(200))
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    n: Mapped[float | None] = mapped_column(Float, default=None)
    p: Mapped[float | None] = mapped_column(Float, default=None)
    k: Mapped[float | None] = mapped_column(Float, default=None)
    carbono_organico: Mapped[float | None] = mapped_column(Float, default=None)
    micronutrientes: Mapped[str | None] = mapped_column(String(300), default=None)
    asesoramento_recibido: Mapped[str | None] = mapped_column(String(300), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    )
```

### Paso 2 — `src/horta/models/__init__.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

Despois:
```python
from horta.models.cultivo import Cultivo
```

### Paso 3 — `src/horta/models/__init__.py`: quitar da lista

Antes:
```python
    "Cultivo",
    "Fertilizacion",
```

Despois:
```python
    "Cultivo",
```

### Paso 4 — crear o ficheiro `alembic/versions/f1e3a5c7b9d2_quitar_fertilizacion_vella.py`

Contido completo:
```python
"""quitar a fertilización vella (substituída por abonado)

Revision ID: f1e3a5c7b9d2
Revises: 230c962c9af9
Create Date: 2026-10-25 02:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1e3a5c7b9d2"
down_revision: Union[str, Sequence[str], None] = "230c962c9af9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("fertilizacion")


def downgrade() -> None:
    op.create_table(
        "fertilizacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("superficie", sa.Float(), nullable=True),
        sa.Column("tipo", sa.String(length=50), nullable=False),
        sa.Column("produto", sa.String(length=200), nullable=False),
        sa.Column("dose", sa.String(length=100), nullable=True),
        sa.Column("n", sa.Float(), nullable=True),
        sa.Column("p", sa.Float(), nullable=True),
        sa.Column("k", sa.Float(), nullable=True),
        sa.Column("carbono_organico", sa.Float(), nullable=True),
        sa.Column("micronutrientes", sa.String(length=300), nullable=True),
        sa.Column("asesoramento_recibido", sa.String(length=300), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cultivo_id"], ["cultivo.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Xa non existe o modelo `Fertilizacion`; a migración borra a táboa `fertilizacion`.
