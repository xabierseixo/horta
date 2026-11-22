# Tarefa 081 — Parte común (1/9): identificador do móbil e base común

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

A parte común dos traballos escríbese unha vez (models/traballo.py) e todos os traballos, a tarefa e o cultivo teñen o identificador do móbil. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `alembic/versions/d7f9b1c3e5a8_parte_comun_uuid.py` (**ficheiro novo**)
- `src/horta/models/traballo.py` (**ficheiro novo**)
- `src/horta/models/labor.py`
- `src/horta/models/analise.py`
- `src/horta/models/tarefa.py`
- `src/horta/models/cultivo.py`
- `src/horta/models/tratamento_fito.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/d7f9b1c3e5a8_parte_comun_uuid.py`

Contido completo:
```python
"""parte común: identificador do móbil en todos os traballos

Revision ID: d7f9b1c3e5a8
Revises: c6e8a0b2d4f7
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f9b1c3e5a8'
down_revision: Union[str, Sequence[str], None] = 'c6e8a0b2d4f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Táboas que aínda non tiñan o identificador do móbil
_SEN_UUID = ("labor", "tratamento_fito", "tratamento_instalacion", "abonado", "rega",
             "analise", "coidado_animal", "movemento_animal", "tarefa", "cultivo")


def upgrade() -> None:
    """Upgrade schema."""
    for taboa in _SEN_UUID:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("uuid", sa.String(length=36), nullable=True))
            batch.create_unique_constraint(f"uq_{taboa}_uuid", ["uuid"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _SEN_UUID:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"uq_{taboa}_uuid", type_="unique")
            batch.drop_column("uuid")
```

### Paso 2 — crear o ficheiro `src/horta/models/traballo.py`

Contido completo:
```python
"""Parte común de todos os traballos (`docs/como-e-a-app.md` §2.4): escríbese unha vez aquí
para que ningún traballo quede sen ela. Cada traballo herda as partes que lle tocan."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column


class ParteComun:
    """Notas, baixa lóxica, identificador do móbil e quen o apuntou: en todos os traballos."""

    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    # Trazabilidade: quen apuntou o traballo
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class FeitoPor:
    """Quen o fixo e cantas horas (no tratamento, cada aplicador)."""

    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)


class ConMaquina:
    """Con que máquina, nos traballos onde pode haber unha."""

    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
```

### Paso 3 — `src/horta/models/labor.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Labor(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Labor(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 4 — `src/horta/models/labor.py`

Antes:
```python
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 5 — `src/horta/models/analise.py`

Antes:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Analise(Base):
```

Despois:
```python
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import FeitoPor, ParteComun


class Analise(ParteComun, FeitoPor, Base):
```

### Paso 6 — `src/horta/models/analise.py`

Antes:
```python
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
```

### Paso 7 — `src/horta/models/analise.py`

Antes:
```python
    cromo: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
    cromo: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 8 — `src/horta/models/tarefa.py`

Antes:
```python
    traballo_id: Mapped[int | None] = mapped_column(Integer, default=None)
```

Despois:
```python
    traballo_id: Mapped[int | None] = mapped_column(Integer, default=None)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
```

### Paso 9 — `src/horta/models/cultivo.py`

Antes:
```python
    sementeira_horas: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    sementeira_horas: Mapped[float | None] = mapped_column(Float, default=None)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
```

### Paso 10 — `src/horta/models/tratamento_fito.py`

Antes:
```python
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
```

Despois:
```python
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (1/9): identificador do móbil e base común: feito.
