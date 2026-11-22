# Tarefa 037 — Parcela completa: datos e regras

**Estado**: pendente

**Rama**: `deseno-visual`. **Depende de**: tarefa 036 (migración `a7d2e5f8c3b1`).

## Obxectivo

Campos obrigatorios do REA bloque 12 para a parcela (= DGC) que faltan segundo `docs/campos-oficiais-anexo-v.md`: agregado e zona SIGPAC, referencia catastral, réxime de tenencia e NIF do arrendador, pequena superficie, datas e causa de alta/baixa; e a orixe da auga (CUE rega). Regras: NIF válido, baixa ≥ alta, códigos de catálogo vixentes. Pantalla noutra tarefa.

## Ficheiros a tocar

- `src/horta/models/parcela.py`
- `alembic/versions/b8e3f6a9d4c2_parcela_completa.py` (**ficheiro novo**)
- `src/horta/services/parcelas.py`
- `tests/services/test_parcelas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/parcela.py`: importar Boolean e Date

Antes:
```python
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
```

Despois:
```python
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Enum, Float, ForeignKey, String, Text
```

### Paso 2 — mesmo ficheiro: campos novos (REA 12, DGC)

Antes:
```python
    sigpac_subparcela: Mapped[str | None] = mapped_column(String(10), default=None)
```

Despois:
```python
    sigpac_subparcela: Mapped[str | None] = mapped_column(String(10), default=None)  # recinto
    # REA bloque 12 (DGC): resto da referencia SIGPAC, catastro, tenencia, alta e baixa
    sigpac_agregado: Mapped[str | None] = mapped_column(String(10), default=None)
    sigpac_zona: Mapped[str | None] = mapped_column(String(10), default=None)
    referencia_catastral: Mapped[str | None] = mapped_column(String(20), default=None)
    rexime_tenencia: Mapped[str | None] = mapped_column(String(20), default=None)
    nif_arrendador: Mapped[str | None] = mapped_column(String(9), default=None)
    pequena_superficie: Mapped[bool] = mapped_column(Boolean, default=False)
    data_alta: Mapped[date | None] = mapped_column(Date, default=None)
    data_baixa: Mapped[date | None] = mapped_column(Date, default=None)
    causa_baixa: Mapped[str | None] = mapped_column(String(20), default=None)
    orixe_auga: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 3 — crear o ficheiro `alembic/versions/b8e3f6a9d4c2_parcela_completa.py`

Contido completo:

```python
"""parcela completa (REA bloque 12, DGC)

Revision ID: b8e3f6a9d4c2
Revises: a7d2e5f8c3b1
Create Date: 2026-10-23 14:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b8e3f6a9d4c2"
down_revision: Union[str, Sequence[str], None] = "a7d2e5f8c3b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("parcela") as batch:
        batch.add_column(sa.Column("sigpac_agregado", sa.String(10), nullable=True))
        batch.add_column(sa.Column("sigpac_zona", sa.String(10), nullable=True))
        batch.add_column(sa.Column("referencia_catastral", sa.String(20), nullable=True))
        batch.add_column(sa.Column("rexime_tenencia", sa.String(20), nullable=True))
        batch.add_column(sa.Column("nif_arrendador", sa.String(9), nullable=True))
        batch.add_column(
            sa.Column("pequena_superficie", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("data_alta", sa.Date(), nullable=True))
        batch.add_column(sa.Column("data_baixa", sa.Date(), nullable=True))
        batch.add_column(sa.Column("causa_baixa", sa.String(20), nullable=True))
        batch.add_column(sa.Column("orixe_auga", sa.String(20), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("parcela") as batch:
        batch.drop_column("orixe_auga")
        batch.drop_column("causa_baixa")
        batch.drop_column("data_baixa")
        batch.drop_column("data_alta")
        batch.drop_column("pequena_superficie")
        batch.drop_column("nif_arrendador")
        batch.drop_column("rexime_tenencia")
        batch.drop_column("referencia_catastral")
        batch.drop_column("sigpac_zona")
        batch.drop_column("sigpac_agregado")
```

### Paso 4 — `src/horta/services/parcelas.py`: campos editables

Antes:
```python
        "sigpac_subparcela",
```

Despois:
```python
        "sigpac_subparcela",
        "sigpac_agregado",
        "sigpac_zona",
        "referencia_catastral",
        "rexime_tenencia",
        "nif_arrendador",
        "pequena_superficie",
        "data_alta",
        "data_baixa",
        "causa_baixa",
        "orixe_auga",
```

### Paso 5 — mesmo ficheiro: importar

Antes:
```python
from typing import Any
```

Despois:
```python
from datetime import date
from typing import Any
```

### Paso 6 — mesmo ficheiro

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.catalogos import validar_codigo
from horta.services.errors import OperacionNonPermitidaError
```

### Paso 7 — mesmo ficheiro

Antes:
```python
from horta.services.hortas import comprobar_rol_horta
```

Despois:
```python
from horta.services.hortas import _PATRON_NIF, comprobar_rol_horta
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
