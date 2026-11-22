# Tarefa 070 — Rexistro de fitosanitarios do MAPA: táboas

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Táboas para gardar dentro de horta o rexistro oficial de produtos fitosanitarios do MAPA (produtos, composición, usos autorizados) e as pontes cos códigos SIEX de cultivos e pragas. Deseño: `docs/superpowers/specs/2026-10-25-tratamentos-completos-design.md` §1.

## Ficheiros a tocar

- `src/horta/models/fito_rexistro.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `alembic/versions/f6b8d0e2a4c7_rexistro_de_fitosanitarios_do_mapa.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/fito_rexistro.py`

Contido completo:
```python
"""Rexistro de produtos fitosanitarios do MAPA (JSON de regfiweb) e pontes cos códigos SIEX."""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class FitoProduto(Base):
    __tablename__ = "fito_produto"

    num_rexistro: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(200), index=True)
    titular: Mapped[str | None] = mapped_column(String(200), default=None)
    estado: Mapped[str | None] = mapped_column(String(20), default=None)
    data_caducidade: Mapped[date | None] = mapped_column(Date, default=None)
    data_cancelacion: Mapped[date | None] = mapped_column(Date, default=None)
    data_limite_venda: Mapped[date | None] = mapped_column(Date, default=None)
    version_id: Mapped[int] = mapped_column(ForeignKey("catalogo_version.id"))


class FitoMateria(Base):
    """Composición: substancia activa e concentración."""

    __tablename__ = "fito_materia"

    id: Mapped[int] = mapped_column(primary_key=True)
    num_rexistro: Mapped[str] = mapped_column(ForeignKey("fito_produto.num_rexistro"),
                                              index=True)
    sustancia: Mapped[str] = mapped_column(String(200))
    concentracion: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(40), default=None)


class FitoUso(Base):
    """Uso autorizado: cultivo × axente × dose × prazo de seguridade (etiqueta)."""

    __tablename__ = "fito_uso"

    id: Mapped[int] = mapped_column(primary_key=True)
    num_rexistro: Mapped[str] = mapped_column(ForeignKey("fito_produto.num_rexistro"),
                                              index=True)
    codigo_cultivo: Mapped[str] = mapped_column(String(16), index=True)
    cultivo: Mapped[str] = mapped_column(String(200))
    codigo_agente: Mapped[str] = mapped_column(String(30))
    agente: Mapped[str] = mapped_column(String(300))
    tipo_usuario: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_cultivo: Mapped[str | None] = mapped_column(String(40), default=None)
    dose_min: Mapped[float | None] = mapped_column(Float, default=None)
    dose_max: Mapped[float | None] = mapped_column(Float, default=None)
    unidade_dose: Mapped[str | None] = mapped_column(String(60), default=None)
    ps_tipo: Mapped[str] = mapped_column(String(20))
    ps_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    aplicacions_max: Mapped[int | None] = mapped_column(Integer, default=None)
    intervalo_min_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    condicionamento: Mapped[str | None] = mapped_column(String(2000), default=None)


class FitoPonteCultivo(Base):
    """Cultivo SIEX → cultivo do MAPA co mesmo código EPPO."""

    __tablename__ = "fito_ponte_cultivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_siex_codigo: Mapped[int] = mapped_column(Integer, index=True)
    codigo_cultivo: Mapped[str] = mapped_column(String(16))


class FitoPonteAxente(Base):
    """Praga, enfermidade, mala herba ou regulador do SIEX → axente do MAPA (nome científico)."""

    __tablename__ = "fito_ponte_axente"

    id: Mapped[int] = mapped_column(primary_key=True)
    catalogo: Mapped[str] = mapped_column(String(20))
    codigo: Mapped[str] = mapped_column(String(20))
    codigo_agente: Mapped[str] = mapped_column(String(30), index=True)
```

### Paso 2 — `src/horta/models/__init__.py`

Antes:
```python
from horta.models.fertilizante import FertilizanteSiex
```

Despois:
```python
from horta.models.fertilizante import FertilizanteSiex
from horta.models.fito_rexistro import (
    FitoMateria,
    FitoPonteAxente,
    FitoPonteCultivo,
    FitoProduto,
    FitoUso,
)
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
    "FertilizanteSiex",
```

Despois:
```python
    "FertilizanteSiex",
    "FitoProduto",
    "FitoMateria",
    "FitoUso",
    "FitoPonteCultivo",
    "FitoPonteAxente",
```

### Paso 4 — crear o ficheiro `alembic/versions/f6b8d0e2a4c7_rexistro_de_fitosanitarios_do_mapa.py`

Contido completo:
```python
"""rexistro de fitosanitarios do MAPA

Revision ID: f6b8d0e2a4c7
Revises: e5a7c9d1f3b6
Create Date: 2026-10-25 09:26:57.962316

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6b8d0e2a4c7'
down_revision: Union[str, Sequence[str], None] = 'e5a7c9d1f3b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fito_ponte_axente',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('catalogo', sa.String(length=20), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.Column('codigo_agente', sa.String(length=30), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fito_ponte_axente_codigo_agente'), 'fito_ponte_axente', ['codigo_agente'], unique=False)
    op.create_table('fito_ponte_cultivo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('cultivo_siex_codigo', sa.Integer(), nullable=False),
    sa.Column('codigo_cultivo', sa.String(length=16), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fito_ponte_cultivo_cultivo_siex_codigo'), 'fito_ponte_cultivo', ['cultivo_siex_codigo'], unique=False)
    op.create_table('fito_produto',
    sa.Column('num_rexistro', sa.String(length=20), nullable=False),
    sa.Column('nome', sa.String(length=200), nullable=False),
    sa.Column('titular', sa.String(length=200), nullable=True),
    sa.Column('estado', sa.String(length=20), nullable=True),
    sa.Column('data_caducidade', sa.Date(), nullable=True),
    sa.Column('data_cancelacion', sa.Date(), nullable=True),
    sa.Column('data_limite_venda', sa.Date(), nullable=True),
    sa.Column('version_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['version_id'], ['catalogo_version.id'], ),
    sa.PrimaryKeyConstraint('num_rexistro')
    )
    op.create_index(op.f('ix_fito_produto_nome'), 'fito_produto', ['nome'], unique=False)
    op.create_table('fito_materia',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('num_rexistro', sa.String(length=20), nullable=False),
    sa.Column('sustancia', sa.String(length=200), nullable=False),
    sa.Column('concentracion', sa.Float(), nullable=True),
    sa.Column('unidade', sa.String(length=40), nullable=True),
    sa.ForeignKeyConstraint(['num_rexistro'], ['fito_produto.num_rexistro'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fito_materia_num_rexistro'), 'fito_materia', ['num_rexistro'], unique=False)
    op.create_table('fito_uso',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('num_rexistro', sa.String(length=20), nullable=False),
    sa.Column('codigo_cultivo', sa.String(length=16), nullable=False),
    sa.Column('cultivo', sa.String(length=200), nullable=False),
    sa.Column('codigo_agente', sa.String(length=30), nullable=False),
    sa.Column('agente', sa.String(length=300), nullable=False),
    sa.Column('tipo_usuario', sa.String(length=20), nullable=True),
    sa.Column('sistema_cultivo', sa.String(length=40), nullable=True),
    sa.Column('dose_min', sa.Float(), nullable=True),
    sa.Column('dose_max', sa.Float(), nullable=True),
    sa.Column('unidade_dose', sa.String(length=60), nullable=True),
    sa.Column('ps_tipo', sa.String(length=20), nullable=False),
    sa.Column('ps_dias', sa.Integer(), nullable=True),
    sa.Column('aplicacions_max', sa.Integer(), nullable=True),
    sa.Column('intervalo_min_dias', sa.Integer(), nullable=True),
    sa.Column('condicionamento', sa.String(length=2000), nullable=True),
    sa.ForeignKeyConstraint(['num_rexistro'], ['fito_produto.num_rexistro'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fito_uso_codigo_cultivo'), 'fito_uso', ['codigo_cultivo'], unique=False)
    op.create_index(op.f('ix_fito_uso_num_rexistro'), 'fito_uso', ['num_rexistro'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_fito_uso_num_rexistro'), table_name='fito_uso')
    op.drop_index(op.f('ix_fito_uso_codigo_cultivo'), table_name='fito_uso')
    op.drop_table('fito_uso')
    op.drop_index(op.f('ix_fito_materia_num_rexistro'), table_name='fito_materia')
    op.drop_table('fito_materia')
    op.drop_index(op.f('ix_fito_produto_nome'), table_name='fito_produto')
    op.drop_table('fito_produto')
    op.drop_index(op.f('ix_fito_ponte_cultivo_cultivo_siex_codigo'), table_name='fito_ponte_cultivo')
    op.drop_table('fito_ponte_cultivo')
    op.drop_index(op.f('ix_fito_ponte_axente_codigo_agente'), table_name='fito_ponte_axente')
    op.drop_table('fito_ponte_axente')
    # ### end Alembic commands ###
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existen as táboas fito_produto, fito_materia, fito_uso, fito_ponte_cultivo e fito_ponte_axente.
