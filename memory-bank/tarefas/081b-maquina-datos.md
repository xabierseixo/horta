# Tarefa 081b — Parte común (3/9): máquina en máis traballos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081a. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Rega, tratamento en instalacións, entradas e saídas e produción poden levar a máquina (a bomba, o remolque, a muxidora); comprobación común de que a máquina é da explotación. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `alembic/versions/e9b1d3f5a7c2_parte_comun_maquina.py` (**ficheiro novo**)
- `src/horta/services/maquinaria.py`
- `src/horta/models/rega.py`
- `src/horta/models/tratamento_instalacion.py`
- `src/horta/models/movemento_animal.py`
- `src/horta/models/producion_animal.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/e9b1d3f5a7c2_parte_comun_maquina.py`

Contido completo:
```python
"""parte común: máquina nos traballos onde pode haber unha

Revision ID: e9b1d3f5a7c2
Revises: d7f9b1c3e5a8
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e9b1d3f5a7c2'
down_revision: Union[str, Sequence[str], None] = 'd7f9b1c3e5a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Traballos onde pode haber unha máquina e aínda non se podía indicar
_SEN_MAQUINA = ("rega", "tratamento_instalacion", "movemento_animal", "producion_animal")


def upgrade() -> None:
    """Upgrade schema."""
    for taboa in _SEN_MAQUINA:
        with op.batch_alter_table(taboa) as batch:
            batch.add_column(sa.Column("maquina_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{taboa}_maquina_id", "maquina", ["maquina_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    for taboa in _SEN_MAQUINA:
        with op.batch_alter_table(taboa) as batch:
            batch.drop_constraint(f"fk_{taboa}_maquina_id", type_="foreignkey")
            batch.drop_column("maquina_id")
```

### Paso 2 — `src/horta/services/maquinaria.py`

Antes:
```python
     "activa", "data_adquisicion"}
)
```

Despois:
```python
     "activa", "data_adquisicion"}
)


def comprobar_maquina(session: Session, horta_id: int, maquina_id: int | None) -> None:
    """A máquina dun traballo (opcional) ten que ser da mesma explotación."""
    if maquina_id is None:
        return
    maquina = session.get(Maquina, maquina_id)
    if maquina is None or maquina.horta_id != horta_id:
        raise OperacionNonPermitidaError("A máquina indicada non é desta explotación")
```

### Paso 3 — `src/horta/models/rega.py`

Antes:
```python
from horta.models.traballo import FeitoPor, ParteComun


class Rega(ParteComun, FeitoPor, Base):
```

Despois:
```python
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class Rega(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 4 — `src/horta/models/tratamento_instalacion.py`

Antes:
```python
from horta.models.traballo import FeitoPor, ParteComun

TIPOS_INSTALACION = {"postcolleita": "Postcolleita (no produto vexetal)",
                     "local": "Local de almacenamento", "transporte": "Medio de transporte"}


class TratamentoInstalacion(ParteComun, FeitoPor, Base):
```

Despois:
```python
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun

TIPOS_INSTALACION = {"postcolleita": "Postcolleita (no produto vexetal)",
                     "local": "Local de almacenamento", "transporte": "Medio de transporte"}


class TratamentoInstalacion(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 5 — `src/horta/models/movemento_animal.py`

Antes:
```python
from horta.models.traballo import FeitoPor, ParteComun


class MovementoAnimal(ParteComun, FeitoPor, Base):
```

Despois:
```python
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class MovementoAnimal(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 6 — `src/horta/models/producion_animal.py`

Antes:
```python
from horta.models.traballo import FeitoPor, ParteComun


class ProducionAnimal(ParteComun, FeitoPor, Base):
```

Despois:
```python
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun


class ProducionAnimal(ParteComun, FeitoPor, ConMaquina, Base):
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (3/9): máquina en máis traballos: feito.
