# Tarefa 053 — Modelo das análises

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Táboas `analise` (de cultivo, produto colleitado, solo ou auga; opcionalmente ligada a parcela, cultivo ou lote da colleita, para a trazabilidade; parámetros do solo do CUE; baixa lóxica), `analise_tipo` e `analise_substancia`. Engádese o catálogo de substancias activas (SUST_ACTIVAS) para as análises de residuos. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §5. Probado no navegador (móbil) o 2026-10-25.

## Ficheiros a tocar

- `src/horta/models/analise.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `alembic/versions/c5e7a9b1d3f6_analises.py` (**ficheiro novo**)
- `src/horta/services/catalogos_importar.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/analise.py`

Contido completo:
```python
"""Análises (CUE bloque 13, se se fixeron): de cultivo, produto colleitado, solo ou auga."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Analise(Base):
    __tablename__ = "analise"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    material_analizado: Mapped[str] = mapped_column(String(20))
    data_mostraxe: Mapped[date] = mapped_column(Date)
    laboratorio: Mapped[str | None] = mapped_column(String(150), default=None)
    laboratorio_nif: Mapped[str | None] = mapped_column(String(9), default=None)
    num_boletin: Mapped[str | None] = mapped_column(String(50), default=None)
    # Onde: opcionais. colleita_id liga a análise do produto co seu lote (trazabilidade).
    parcela_id: Mapped[int | None] = mapped_column(ForeignKey("parcela.id"), default=None)
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    colleita_id: Mapped[int | None] = mapped_column(ForeignKey("colleita.id"), default=None)
    # Parámetros do solo (CUE ParametrosSuelo): só se o material é solo
    materia_organica: Mapped[float | None] = mapped_column(Float, default=None)
    area: Mapped[float | None] = mapped_column(Float, default=None)
    limo: Mapped[float | None] = mapped_column(Float, default=None)
    arxila: Mapped[float | None] = mapped_column(Float, default=None)
    ph: Mapped[float | None] = mapped_column(Float, default=None)
    fosforo_ppm: Mapped[float | None] = mapped_column(Float, default=None)
    potasio_ppm: Mapped[float | None] = mapped_column(Float, default=None)
    n_total: Mapped[float | None] = mapped_column(Float, default=None)
    conductividade: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    tipos: Mapped[list[AnaliseTipo]] = relationship(cascade="all, delete-orphan")
    substancias: Mapped[list[AnaliseSubstancia]] = relationship(cascade="all, delete-orphan")


class AnaliseTipo(Base):
    __tablename__ = "analise_tipo"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))


class AnaliseSubstancia(Base):
    __tablename__ = "analise_substancia"

    id: Mapped[int] = mapped_column(primary_key=True)
    analise_id: Mapped[int] = mapped_column(ForeignKey("analise.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
```

### Paso 2 — `src/horta/models/__init__.py`: importar

Antes:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
from horta.models.analise import Analise, AnaliseSubstancia, AnaliseTipo
```

### Paso 3 — `src/horta/models/__init__.py`: engadir á lista

Antes:
```python
    "RegaBoaPractica",
```

Despois:
```python
    "RegaBoaPractica",
    "Analise",
    "AnaliseTipo",
    "AnaliseSubstancia",
```

### Paso 4 — crear o ficheiro `alembic/versions/c5e7a9b1d3f6_analises.py`

Contido completo:
```python
"""analises

Revision ID: c5e7a9b1d3f6
Revises: b4d6f8a0c2e5
Create Date: 2026-10-25 02:49:02.383048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5e7a9b1d3f6'
down_revision: Union[str, Sequence[str], None] = 'b4d6f8a0c2e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('analise',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('horta_id', sa.Integer(), nullable=False),
    sa.Column('material_analizado', sa.String(length=20), nullable=False),
    sa.Column('data_mostraxe', sa.Date(), nullable=False),
    sa.Column('laboratorio', sa.String(length=150), nullable=True),
    sa.Column('laboratorio_nif', sa.String(length=9), nullable=True),
    sa.Column('num_boletin', sa.String(length=50), nullable=True),
    sa.Column('parcela_id', sa.Integer(), nullable=True),
    sa.Column('cultivo_id', sa.Integer(), nullable=True),
    sa.Column('colleita_id', sa.Integer(), nullable=True),
    sa.Column('materia_organica', sa.Float(), nullable=True),
    sa.Column('area', sa.Float(), nullable=True),
    sa.Column('limo', sa.Float(), nullable=True),
    sa.Column('arxila', sa.Float(), nullable=True),
    sa.Column('ph', sa.Float(), nullable=True),
    sa.Column('fosforo_ppm', sa.Float(), nullable=True),
    sa.Column('potasio_ppm', sa.Float(), nullable=True),
    sa.Column('n_total', sa.Float(), nullable=True),
    sa.Column('conductividade', sa.Float(), nullable=True),
    sa.Column('notas', sa.String(length=1000), nullable=True),
    sa.Column('baixa', sa.Boolean(), nullable=False),
    sa.Column('creado_por', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['colleita_id'], ['colleita.id'], ),
    sa.ForeignKeyConstraint(['creado_por'], ['usuario.id'], ),
    sa.ForeignKeyConstraint(['cultivo_id'], ['cultivo.id'], ),
    sa.ForeignKeyConstraint(['horta_id'], ['horta.id'], ),
    sa.ForeignKeyConstraint(['parcela_id'], ['parcela.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analise_horta_id'), 'analise', ['horta_id'], unique=False)
    op.create_table('analise_substancia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('analise_id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['analise_id'], ['analise.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analise_substancia_analise_id'), 'analise_substancia', ['analise_id'], unique=False)
    op.create_table('analise_tipo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('analise_id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['analise_id'], ['analise.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_analise_tipo_analise_id'), 'analise_tipo', ['analise_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_analise_tipo_analise_id'), table_name='analise_tipo')
    op.drop_table('analise_tipo')
    op.drop_index(op.f('ix_analise_substancia_analise_id'), table_name='analise_substancia')
    op.drop_table('analise_substancia')
    op.drop_index(op.f('ix_analise_horta_id'), table_name='analise')
    op.drop_table('analise')
    # ### end Alembic commands ###
```

### Paso 5 — `src/horta/services/catalogos_importar.py`: catálogo de substancias activas

Antes:
```python
    "sistema_rega": ("SIST_RIEGO", "Código SIEX", None),
```

Despois:
```python
    "sistema_rega": ("SIST_RIEGO", "Código SIEX", None),
    "substancia_activa": ("SUST_ACTIVAS", "Código SIEX", "Sustancia"),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existen as táboas das análises e impórtase o catálogo de substancias activas.
