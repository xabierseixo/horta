# Tarefa 042e — Quitar o modelo e a táboa do tratamento vello

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 042d (e de que Claude borre `services/tratamentos.py` e `tests/services/test_tratamentos.py`).

## Obxectivo

O modelo vello `Tratamento` (táboa `tratamento`) xa non o usa ningunha pantalla: os datos pasaron a `TratamentoFito` (caderno CUE). Paso 5 de 5: quitar a clase e borrar a táboa cunha migración (a volta atrás crea a táboa baleira).

## Ficheiros a tocar

- `src/horta/models/cultivo.py`
- `src/horta/models/__init__.py`
- `alembic/versions/c7f2a9d1e4b6_quitar_tratamento_vello.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros. Non executes `alembic revision`.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/cultivo.py`: quitar a clase

Antes:
```python
class Tratamento(Base):
    __tablename__ = "tratamento"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"))
    data: Mapped[date] = mapped_column(Date)
    praga: Mapped[str] = mapped_column(String(200))
    superficie_tratada: Mapped[float | None] = mapped_column(Float, default=None)
    produto: Mapped[str] = mapped_column(String(200))
    numero_rexistro_produto: Mapped[str | None] = mapped_column(String(50), default=None)
    dose: Mapped[str | None] = mapped_column(String(100), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(200), default=None)
    aplicador: Mapped[str] = mapped_column(String(200))
    equipo_aplicador: Mapped[str | None] = mapped_column(String(200), default=None)
    persoas_asesoramento: Mapped[str | None] = mapped_column(String(200), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Fertilizacion(Base):
```

Despois:
```python
class Fertilizacion(Base):
```

### Paso 2 — `src/horta/models/__init__.py`: importar

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.cultivo import Cultivo, Fertilizacion
```

### Paso 3 — `src/horta/models/__init__.py`: quitar da lista

Antes:
```python
    "Cultivo",
    "Tratamento",
```

Despois:
```python
    "Cultivo",
```

### Paso 4 — crear o ficheiro `alembic/versions/c7f2a9d1e4b6_quitar_tratamento_vello.py`

Contido completo:
```python
"""quitar o tratamento vello (os datos están en tratamento_fito)

Revision ID: c7f2a9d1e4b6
Revises: b8e3f6a9d4c2
Create Date: 2026-10-24 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c7f2a9d1e4b6"
down_revision: Union[str, Sequence[str], None] = "b8e3f6a9d4c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("tratamento")


def downgrade() -> None:
    op.create_table(
        "tratamento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cultivo_id", sa.Integer(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("praga", sa.String(length=200), nullable=False),
        sa.Column("superficie_tratada", sa.Float(), nullable=True),
        sa.Column("produto", sa.String(length=200), nullable=False),
        sa.Column("numero_rexistro_produto", sa.String(length=50), nullable=True),
        sa.Column("dose", sa.String(length=100), nullable=True),
        sa.Column("eficacia", sa.String(length=200), nullable=True),
        sa.Column("aplicador", sa.String(length=200), nullable=False),
        sa.Column("equipo_aplicador", sa.String(length=200), nullable=True),
        sa.Column("persoas_asesoramento", sa.String(length=200), nullable=True),
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

Xa non existe o modelo vello `Tratamento`; a migración borra a táboa `tratamento`.
