# Tarefa 075 — Quen e horas (1/2 datos): rega, colleita, mostras e instalacións

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos, rega, colleita, toma de mostras e tratamento en instalacións gardan quen o fixo e cantas horas (migración para todos os tipos). Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `alembic/versions/d0a2c4e6f8b1_quen_e_horas.py` (**ficheiro novo**)
- `src/horta/models/rega.py`
- `src/horta/models/colleita.py`
- `src/horta/models/analise.py`
- `src/horta/models/tratamento_instalacion.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/d0a2c4e6f8b1_quen_e_horas.py`

Contido completo:
```python
"""quen fixo cada traballo e cantas horas

Revision ID: d0a2c4e6f8b1
Revises: c9e1a3b5d7f0
Create Date: 2026-10-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0a2c4e6f8b1'
down_revision: Union[str, Sequence[str], None] = 'c9e1a3b5d7f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Táboa -> (columna da persoa ou None se xa a ten, columna das horas)
_COLUMNAS = {
    "rega": ("persoa_id", "horas"),
    "colleita": ("persoa_id", "horas"),
    "analise": ("persoa_id", "horas"),
    "tratamento_instalacion": ("persoa_id", "horas"),
    "labor": (None, "horas"),
    "abonado": (None, "horas"),
    "cultivo": ("sementeira_persoa_id", "sementeira_horas"),
}


def upgrade() -> None:
    """Upgrade schema."""
    for taboa, (persoa, horas) in _COLUMNAS.items():
        with op.batch_alter_table(taboa) as batch:
            if persoa:
                batch.add_column(sa.Column(persoa, sa.Integer(), nullable=True))
                batch.create_foreign_key(f"fk_{taboa}_{persoa}", "persoa", [persoa], ["id"])
            batch.add_column(sa.Column(horas, sa.Float(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    for taboa, (persoa, horas) in _COLUMNAS.items():
        with op.batch_alter_table(taboa) as batch:
            batch.drop_column(horas)
            if persoa:
                batch.drop_constraint(f"fk_{taboa}_{persoa}", type_="foreignkey")
                batch.drop_column(persoa)
```

### Paso 2 — `src/horta/models/rega.py`

Antes:
```python
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)
```

Despois:
```python
    num_contador: Mapped[str | None] = mapped_column(String(14), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 3 — `src/horta/models/colleita.py`

Antes:
```python
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 4 — `src/horta/models/analise.py`

Antes:
```python
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
```

Despois:
```python
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 5 — `src/horta/models/tratamento_instalacion.py`

Antes:
```python
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
```

Despois:
```python
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Quen e horas (1/2 datos): rega, colleita, mostras e instalacións: feito.
