# Tarefa 074 — Apuntar o mínimo (1/6): rega con datos opcionais

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na rega, a superficie, o sistema e a cantidade de auga pasan a ser opcionais na base de datos (migración para rega, labor e abonado). O caderno e a táboa de regas aceptan que falten. Deseño: `docs/superpowers/specs/2026-10-26-diario-de-traballos-design.md`

## Ficheiros a tocar

- `src/horta/models/rega.py`
- `alembic/versions/c9e1a3b5d7f0_campos_opcionais.py` (**ficheiro novo**)
- `src/horta/services/caderno.py`
- `src/horta/ui/pages/regas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/rega.py`

Antes:
```python
    superficie_ha: Mapped[float] = mapped_column(Float)
    sistema_rega: Mapped[str] = mapped_column(String(20))
    cantidade: Mapped[float] = mapped_column(Float)
```

Despois:
```python
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    sistema_rega: Mapped[str | None] = mapped_column(String(20), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
```

### Paso 2 — crear o ficheiro `alembic/versions/c9e1a3b5d7f0_campos_opcionais.py`

Contido completo:
```python
"""campos do CUE opcionais ao apuntar (o caderno avisa do que falta)

Revision ID: c9e1a3b5d7f0
Revises: b8d0f2a4c6e9
Create Date: 2026-10-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9e1a3b5d7f0'
down_revision: Union[str, Sequence[str], None] = 'b8d0f2a4c6e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_OPCIONAIS = {
    "rega": (("superficie_ha", sa.Float()), ("sistema_rega", sa.String(length=20)),
             ("cantidade", sa.Float())),
    "labor": (("superficie_ha", sa.Float()),),
    "abonado": (("superficie_ha", sa.Float()), ("tipo_fertilizacion", sa.String(length=20)),
                ("metodo", sa.String(length=20))),
}


def upgrade() -> None:
    """Upgrade schema."""
    for taboa, columnas in _OPCIONAIS.items():
        with op.batch_alter_table(taboa) as batch:
            for nome, tipo in columnas:
                batch.alter_column(nome, existing_type=tipo, nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    for taboa, columnas in _OPCIONAIS.items():
        with op.batch_alter_table(taboa) as batch:
            for nome, tipo in columnas:
                batch.alter_column(nome, existing_type=tipo, nullable=False)
```

### Paso 3 — `src/horta/services/caderno.py`

Antes:
```python
                 if r.superficie_ha else None)
```

Despois:
```python
                 if r.superficie_ha and r.cantidade else None)
```

### Paso 4 — `src/horta/services/caderno.py`

Antes:
```python
            describir(session, "sistema_rega", r.sistema_rega),
```

Despois:
```python
            describir(session, "sistema_rega", r.sistema_rega) if r.sistema_rega else "",
```

### Paso 5 — `src/horta/ui/pages/regas.py`

Antes:
```python
        "sistema": sistemas.get(r.sistema_rega, r.sistema_rega),
        "auga": f"{r.cantidade:g} {unidades.get(r.unidade, '')}",
```

Despois:
```python
        "sistema": sistemas.get(r.sistema_rega, r.sistema_rega) if r.sistema_rega else "",
        "auga": f"{r.cantidade:g} {unidades.get(r.unidade, '')}" if r.cantidade else "",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Apuntar o mínimo (1/6): rega con datos opcionais: feito.
