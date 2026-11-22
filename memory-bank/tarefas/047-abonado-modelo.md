# Tarefa 047 — Modelos de abonos e abonados

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 046. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Táboas novas da fertilización: `fertilizante` (os abonos de cada explotación, gardados unha vez), `abonado` (cada aplicación a un cultivo, baixa lóxica) e `abonado_boa_practica` (as boas prácticas de cada abonado, obrigatorias no CUE). A táboa vella `fertilizacion` quitarase despois. Deseño: `docs/superpowers/specs/2026-10-25-caderno-fase2-fertilizacion-rega-design.md` §1–2.

## Ficheiros a tocar

- `src/horta/models/abonado.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `alembic/versions/230c962c9af9_abonados.py` (**ficheiro novo**)

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/abonado.py`

Contido completo:
```python
"""Fertilización (CUE bloque 9): os abonos de cada explotación e cada abonado. Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base


class Fertilizante(Base):
    """Un abono da explotación ("Os meus abonos"): gárdase unha vez e escóllese ao abonar."""

    __tablename__ = "fertilizante"
    __table_args__ = (UniqueConstraint("horta_id", "nome"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    nome: Mapped[str] = mapped_column(String(250))
    material: Mapped[str] = mapped_column(String(20))
    fertilizante_siex_codigo: Mapped[int | None] = mapped_column(
        ForeignKey("fertilizante_siex.codigo"), default=None
    )
    n_pct: Mapped[float | None] = mapped_column(Float, default=None)
    p2o5_pct: Mapped[float | None] = mapped_column(Float, default=None)
    k2o_pct: Mapped[float | None] = mapped_column(Float, default=None)
    liquido: Mapped[bool] = mapped_column(Boolean, default=False)
    densidade: Mapped[float | None] = mapped_column(Float, default=None)  # kg/L
    tratamento_estercos: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_nome: Mapped[str | None] = mapped_column(String(150), default=None)
    provedor_nif: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_rega: Mapped[str | None] = mapped_column(String(14), default=None)
    provedor_nima: Mapped[str | None] = mapped_column(String(50), default=None)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Abonado(Base):
    """Cada aplicación de abono a un cultivo."""

    __tablename__ = "abonado"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    superficie_ha: Mapped[float] = mapped_column(Float)
    fertilizante_id: Mapped[int | None] = mapped_column(ForeignKey("fertilizante.id"), default=None)
    dose: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    tipo_fertilizacion: Mapped[str] = mapped_column(String(20))
    metodo: Mapped[str] = mapped_column(String(20))
    xestion_sostible: Mapped[bool] = mapped_column(Boolean, default=False)
    aplicacion_lodos: Mapped[bool] = mapped_column(Boolean, default=False)
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
    aplicador_persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    empresa_servizos_regfer: Mapped[str | None] = mapped_column(String(50), default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    boas_practicas: Mapped[list[AbonadoBoaPractica]] = relationship(
        cascade="all, delete-orphan"
    )


class AbonadoBoaPractica(Base):
    __tablename__ = "abonado_boa_practica"

    id: Mapped[int] = mapped_column(primary_key=True)
    abonado_id: Mapped[int] = mapped_column(ForeignKey("abonado.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(20))
```

### Paso 2 — `src/horta/models/__init__.py`: importar

Antes:
```python
from horta.models.animal import```

Despois:
```python
from horta.models.abonado import Abonado, AbonadoBoaPractica, Fertilizante
from horta.models.animal import```

### Paso 3 — `src/horta/models/__init__.py`: engadir á lista

Antes:
```python
    "FertilizanteSiex",
```

Despois:
```python
    "FertilizanteSiex",
    "Fertilizante",
    "Abonado",
    "AbonadoBoaPractica",
```

### Paso 4 — crear o ficheiro `alembic/versions/230c962c9af9_abonados.py`

Contido completo:
```python
"""abonados

Revision ID: 230c962c9af9
Revises: d8a1f3c5e7b9
Create Date: 2026-10-25 01:15:56.379202

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '230c962c9af9'
down_revision: Union[str, Sequence[str], None] = 'd8a1f3c5e7b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('fertilizante',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('horta_id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=250), nullable=False),
    sa.Column('material', sa.String(length=20), nullable=False),
    sa.Column('fertilizante_siex_codigo', sa.Integer(), nullable=True),
    sa.Column('n_pct', sa.Float(), nullable=True),
    sa.Column('p2o5_pct', sa.Float(), nullable=True),
    sa.Column('k2o_pct', sa.Float(), nullable=True),
    sa.Column('liquido', sa.Boolean(), nullable=False),
    sa.Column('densidade', sa.Float(), nullable=True),
    sa.Column('tratamento_estercos', sa.String(length=20), nullable=True),
    sa.Column('provedor_nome', sa.String(length=150), nullable=True),
    sa.Column('provedor_nif', sa.String(length=14), nullable=True),
    sa.Column('provedor_rega', sa.String(length=14), nullable=True),
    sa.Column('provedor_nima', sa.String(length=50), nullable=True),
    sa.Column('activo', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['fertilizante_siex_codigo'], ['fertilizante_siex.codigo'], ),
    sa.ForeignKeyConstraint(['horta_id'], ['horta.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('horta_id', 'nome')
    )
    op.create_index(op.f('ix_fertilizante_horta_id'), 'fertilizante', ['horta_id'], unique=False)
    op.create_table('abonado',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('horta_id', sa.Integer(), nullable=False),
    sa.Column('cultivo_id', sa.Integer(), nullable=False),
    sa.Column('data_inicio', sa.Date(), nullable=False),
    sa.Column('data_fin', sa.Date(), nullable=False),
    sa.Column('superficie_ha', sa.Float(), nullable=False),
    sa.Column('fertilizante_id', sa.Integer(), nullable=True),
    sa.Column('dose', sa.Float(), nullable=True),
    sa.Column('unidade', sa.String(length=20), nullable=True),
    sa.Column('tipo_fertilizacion', sa.String(length=20), nullable=False),
    sa.Column('metodo', sa.String(length=20), nullable=False),
    sa.Column('xestion_sostible', sa.Boolean(), nullable=False),
    sa.Column('aplicacion_lodos', sa.Boolean(), nullable=False),
    sa.Column('albaran_factura', sa.String(length=50), nullable=True),
    sa.Column('aplicador_persoa_id', sa.Integer(), nullable=True),
    sa.Column('empresa_servizos_regfer', sa.String(length=50), nullable=True),
    sa.Column('maquina_id', sa.Integer(), nullable=True),
    sa.Column('num_repeticions', sa.Integer(), nullable=True),
    sa.Column('duracion_h_ha', sa.Float(), nullable=True),
    sa.Column('notas', sa.String(length=1000), nullable=True),
    sa.Column('baixa', sa.Boolean(), nullable=False),
    sa.Column('creado_por', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['aplicador_persoa_id'], ['persoa.id'], ),
    sa.ForeignKeyConstraint(['creado_por'], ['usuario.id'], ),
    sa.ForeignKeyConstraint(['cultivo_id'], ['cultivo.id'], ),
    sa.ForeignKeyConstraint(['fertilizante_id'], ['fertilizante.id'], ),
    sa.ForeignKeyConstraint(['horta_id'], ['horta.id'], ),
    sa.ForeignKeyConstraint(['maquina_id'], ['maquina.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_abonado_cultivo_id'), 'abonado', ['cultivo_id'], unique=False)
    op.create_index(op.f('ix_abonado_horta_id'), 'abonado', ['horta_id'], unique=False)
    op.create_table('abonado_boa_practica',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('abonado_id', sa.Integer(), nullable=False),
    sa.Column('codigo', sa.String(length=20), nullable=False),
    sa.ForeignKeyConstraint(['abonado_id'], ['abonado.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_abonado_boa_practica_abonado_id'), 'abonado_boa_practica', ['abonado_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_abonado_boa_practica_abonado_id'), table_name='abonado_boa_practica')
    op.drop_table('abonado_boa_practica')
    op.drop_index(op.f('ix_abonado_horta_id'), table_name='abonado')
    op.drop_index(op.f('ix_abonado_cultivo_id'), table_name='abonado')
    op.drop_table('abonado')
    op.drop_index(op.f('ix_fertilizante_horta_id'), table_name='fertilizante')
    op.drop_table('fertilizante')
    # ### end Alembic commands ###
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Existen as táboas `fertilizante`, `abonado` e `abonado_boa_practica`.
