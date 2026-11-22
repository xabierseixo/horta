# Tarefa 076 — Tarefas por facer (1/16 datos): tipo, quen, horas e traballo apuntado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos, a tarefa garda o tipo de traballo, quen o vai facer, as horas e o traballo apuntado ao facela. Deseño: `docs/superpowers/specs/2026-10-27-tarefas-traballos-por-facer-design.md`

## Ficheiros a tocar

- `alembic/versions/e1b3d5f7a9c2_tarefas_traballos_por_facer.py` (**ficheiro novo**)
- `src/horta/models/tarefa.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/e1b3d5f7a9c2_tarefas_traballos_por_facer.py`

Contido completo:
```python
"""tarefas = traballos por facer: tipo, quen, horas e o traballo apuntado

Revision ID: e1b3d5f7a9c2
Revises: d0a2c4e6f8b1
Create Date: 2026-10-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1b3d5f7a9c2'
down_revision: Union[str, Sequence[str], None] = 'd0a2c4e6f8b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.add_column(sa.Column("tipo", sa.String(length=30), nullable=True))
        batch.add_column(sa.Column("persoa_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tarefa_persoa_id", "persoa", ["persoa_id"], ["id"])
        batch.add_column(sa.Column("horas", sa.Float(), nullable=True))
        batch.add_column(sa.Column("traballo_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.drop_column("traballo_id")
        batch.drop_column("horas")
        batch.drop_constraint("fk_tarefa_persoa_id", type_="foreignkey")
        batch.drop_column("persoa_id")
        batch.drop_column("tipo")
```

### Paso 2 — `src/horta/models/tarefa.py`

Antes:
```python
from sqlalchemy import Date, DateTime, ForeignKey, String
```

Despois:
```python
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String
```

### Paso 3 — `src/horta/models/tarefa.py`

Antes:
```python
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
```

Despois:
```python
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    # Traballo por facer: o seu tipo (services.tarefas.TIPOS_TAREFA; baleiro = outro traballo)
    tipo: Mapped[str | None] = mapped_column(String(30), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    # Ao facela: o rexistro apuntado na táboa do seu tipo
    traballo_id: Mapped[int | None] = mapped_column(Integer, default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Tarefas por facer (1/16 datos): tipo, quen, horas e traballo apuntado: feito.
