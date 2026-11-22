# Tarefa 077 — Coidado dos animais (1/10 datos): táboa de coidados e animais na tarefa

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Na base de datos hai unha táboa para os coidados, enfermidades, cambios na produción, medicamentos e visitas de cada grupo de animais; a tarefa pode referirse a un grupo de animais. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `alembic/versions/f3a5c7e9b1d4_coidado_animal.py` (**ficheiro novo**)
- `src/horta/models/coidado_animal.py` (**ficheiro novo**)
- `src/horta/models/__init__.py`
- `src/horta/models/tarefa.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/f3a5c7e9b1d4_coidado_animal.py`

Contido completo:
```python
"""coidado e saúde dos animais; a tarefa pode referirse a un grupo de animais

Revision ID: f3a5c7e9b1d4
Revises: e1b3d5f7a9c2
Create Date: 2026-10-28 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a5c7e9b1d4'
down_revision: Union[str, Sequence[str], None] = 'e1b3d5f7a9c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "coidado_animal",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("horta_id", sa.Integer(), nullable=False),
        sa.Column("animal_id", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=False),
        sa.Column("tipo", sa.String(length=20), nullable=False),
        sa.Column("descricion", sa.String(length=500), nullable=True),
        sa.Column("num_animais", sa.Integer(), nullable=True),
        sa.Column("identificacion", sa.String(length=500), nullable=True),
        sa.Column("medicamento", sa.String(length=250), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=True),
        sa.Column("unidade", sa.String(length=20), nullable=True),
        sa.Column("provedor", sa.String(length=300), nullable=True),
        sa.Column("proba_compra", sa.String(length=100), nullable=True),
        sa.Column("veterinario", sa.String(length=200), nullable=True),
        sa.Column("receita", sa.String(length=50), nullable=True),
        sa.Column("tempo_espera_dias", sa.Integer(), nullable=True),
        sa.Column("duracion_dias", sa.Integer(), nullable=True),
        sa.Column("visitante", sa.String(length=200), nullable=True),
        sa.Column("matricula", sa.String(length=20), nullable=True),
        sa.Column("persoa_id", sa.Integer(), nullable=True),
        sa.Column("horas", sa.Float(), nullable=True),
        sa.Column("maquina_id", sa.Integer(), nullable=True),
        sa.Column("notas", sa.String(length=1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False),
        sa.Column("creado_por", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["horta_id"], ["horta.id"]),
        sa.ForeignKeyConstraint(["animal_id"], ["animal.id"]),
        sa.ForeignKeyConstraint(["persoa_id"], ["persoa.id"]),
        sa.ForeignKeyConstraint(["maquina_id"], ["maquina.id"]),
        sa.ForeignKeyConstraint(["creado_por"], ["usuario.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_coidado_animal_horta_id", "coidado_animal", ["horta_id"])
    op.create_index("ix_coidado_animal_animal_id", "coidado_animal", ["animal_id"])
    with op.batch_alter_table("tarefa") as batch:
        batch.add_column(sa.Column("animal_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tarefa_animal_id", "animal", ["animal_id"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tarefa") as batch:
        batch.drop_constraint("fk_tarefa_animal_id", type_="foreignkey")
        batch.drop_column("animal_id")
    op.drop_index("ix_coidado_animal_animal_id", table_name="coidado_animal")
    op.drop_index("ix_coidado_animal_horta_id", table_name="coidado_animal")
    op.drop_table("coidado_animal")
```

### Paso 2 — crear o ficheiro `src/horta/models/coidado_animal.py`

Contido completo:
```python
"""Coidado e saúde dos animais: cada coidado, enfermidade, cambio na produción, medicamento
ou visita dun grupo de animais (libro de rexistro gandeiro, RD 787/2023 anexo V 6, 7 e 11;
medicamentos, Reg. UE 2019/6 art. 108). Baixa lóxica."""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class CoidadoAnimal(Base):
    __tablename__ = "coidado_animal"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    animal_id: Mapped[int] = mapped_column(ForeignKey("animal.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    # services.coidados_animais.TIPOS_COIDADO
    tipo: Mapped[str] = mapped_column(String(20))
    descricion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Enfermidade, cambio na produción e medicamento: animais afectados ou tratados
    num_animais: Mapped[int | None] = mapped_column(Integer, default=None)
    identificacion: Mapped[str | None] = mapped_column(String(500), default=None)
    # Medicamento
    medicamento: Mapped[str | None] = mapped_column(String(250), default=None)
    cantidade: Mapped[float | None] = mapped_column(Float, default=None)
    unidade: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor: Mapped[str | None] = mapped_column(String(300), default=None)
    proba_compra: Mapped[str | None] = mapped_column(String(100), default=None)
    veterinario: Mapped[str | None] = mapped_column(String(200), default=None)
    receita: Mapped[str | None] = mapped_column(String(50), default=None)
    tempo_espera_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    # Visita ou vehículo
    visitante: Mapped[str | None] = mapped_column(String(200), default=None)
    matricula: Mapped[str | None] = mapped_column(String(20), default=None)
    # Parte común
    persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

### Paso 3 — `src/horta/models/__init__.py`

Antes:
```python
    VariedadeSiex,
)
```

Despois:
```python
    VariedadeSiex,
)
from horta.models.coidado_animal import CoidadoAnimal
```

### Paso 4 — `src/horta/models/__init__.py`

Antes:
```python
    "Animal",
```

Despois:
```python
    "Animal",
    "CoidadoAnimal",
```

### Paso 5 — `src/horta/models/tarefa.py`

Antes:
```python
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
```

Despois:
```python
    cultivo_id: Mapped[int | None] = mapped_column(ForeignKey("cultivo.id"), default=None)
    animal_id: Mapped[int | None] = mapped_column(ForeignKey("animal.id"), default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (1/10 datos): táboa de coidados e animais na tarefa: feito.
