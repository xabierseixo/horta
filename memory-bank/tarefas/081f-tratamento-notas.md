# Tarefa 081f — Parte común (7/9): notas e quen apuntou o tratamento

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As observacións do tratamento pasan a ser as súas notas, e gárdase quen o apuntou. Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `alembic/versions/a1d3f5b7c9e4_tratamento_notas.py` (**ficheiro novo**)
- `src/horta/services/tratamentos_fito.py`
- `src/horta/ui/dialogo_tratamento.py`
- `src/horta/ui/pages/tratamentos.py`
- `tests/test_migracion_tratamento_fito.py`
- `tests/services/test_tratamentos_fito.py`
- `src/horta/models/tratamento_fito.py`
- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/a1d3f5b7c9e4_tratamento_notas.py`

Contido completo:
```python
"""parte común no tratamento: as observacións son as notas; quen o apuntou

Revision ID: a1d3f5b7c9e4
Revises: f0c2e4a6b8d3
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1d3f5b7c9e4'
down_revision: Union[str, Sequence[str], None] = 'f0c2e4a6b8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("tratamento_fito") as batch:
        batch.alter_column("observacions", new_column_name="notas")
        batch.add_column(sa.Column("creado_por", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_tratamento_fito_creado_por", "usuario",
                                 ["creado_por"], ["id"])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("tratamento_fito") as batch:
        batch.drop_constraint("fk_tratamento_fito_creado_por", type_="foreignkey")
        batch.drop_column("creado_por")
        batch.alter_column("notas", new_column_name="observacions")
```

### Paso 2 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
    eficacia: str | None = None
    observacions: str | None = None
```

Despois:
```python
    eficacia: str | None = None
    notas: str | None = None
```

### Paso 3 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
    tratamento.observacions = datos.observacions
```

Despois:
```python
    tratamento.notas = datos.notas
```

### Paso 4 — `src/horta/services/tratamentos_fito.py`

Antes:
```python
                                data_fin=datos.data_fin)
```

Despois:
```python
                                data_fin=datos.data_fin, creado_por=actor.id)
```

### Paso 5 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
                observacions = ui.textarea("Observacións").classes("w-full")
```

Despois:
```python
                notas = ui.textarea("Notas").classes("w-full")
```

### Paso 6 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
                        observacions=observacions.value or None,
```

Despois:
```python
                        notas=notas.value or None,
```

### Paso 7 — `src/horta/ui/dialogo_tratamento.py`

Antes:
```python
        observacions.value = (t.observacions or "") if t else ""
```

Despois:
```python
        notas.value = (t.notas or "") if t else ""
```

### Paso 8 — `src/horta/ui/pages/tratamentos.py`

Antes:
```python
                or (t.observacions or ""),
```

Despois:
```python
                or (t.notas or ""),
```

### Paso 9 — `tests/test_migracion_tratamento_fito.py`

Antes:
```python
            "orixinal_aplicador, observacions, tratamento_antigo_id, baixa FROM tratamento_fito"
        )).mappings().one()
        cultivo = conn.execute(text(
            "SELECT cultivo_id, superficie_ha FROM tratamento_cultivo WHERE tratamento_id = :t"
        ), {"t": fito["id"]}).mappings().one()
    assert fito["horta_id"] == 1
    assert str(fito["data_inicio"]) == "2026-05-01"
    assert (fito["orixinal_produto"], fito["orixinal_dose"], fito["orixinal_aplicador"]) == (
        "Cobre", "2 kg/ha", "Xan"
    )
    assert "Mildeu" in fito["observacions"] and "ES-1" in fito["observacions"]
```

Despois:
```python
            "orixinal_aplicador, notas, tratamento_antigo_id, baixa FROM tratamento_fito"
        )).mappings().one()
        cultivo = conn.execute(text(
            "SELECT cultivo_id, superficie_ha FROM tratamento_cultivo WHERE tratamento_id = :t"
        ), {"t": fito["id"]}).mappings().one()
    assert fito["horta_id"] == 1
    assert str(fito["data_inicio"]) == "2026-05-01"
    assert (fito["orixinal_produto"], fito["orixinal_dose"], fito["orixinal_aplicador"]) == (
        "Cobre", "2 kg/ha", "Xan"
    )
    assert "Mildeu" in fito["notas"] and "ES-1" in fito["notas"]
```

### Paso 10 — `tests/services/test_tratamentos_fito.py`

Antes:
```python
    t = crear_tratamento_fito(session, ana, horta.id, _datos(cultivo, xan, maquina))
    assert [c.cultivo_id for c in t.cultivos] == [cultivo.id]
    assert faltas_para_cue(t) == []
```

Despois:
```python
    datos = _datos(cultivo, xan, maquina)
    datos.notas = "Sen vento"
    t = crear_tratamento_fito(session, ana, horta.id, datos)
    assert [c.cultivo_id for c in t.cultivos] == [cultivo.id]
    assert faltas_para_cue(t) == []
    # Parte común: as notas e quen o apuntou, como nos outros traballos
    assert t.notas == "Sen vento" and t.creado_por == ana.id
```

### Paso 11 — `src/horta/models/tratamento_fito.py`

Antes:
```python
from datetime import date, datetime, time, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base

TIPOS_PROBLEMA = ("enfermidade", "praga", "mala_herba", "regulador")


class TratamentoFito(Base):
    __tablename__ = "tratamento_fito"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    hora: Mapped[time | None] = mapped_column(Time, default=None)
    actividade_cuberta: Mapped[str | None] = mapped_column(String(20), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(20), default=None)
    observacions: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

Despois:
```python
from datetime import date, time

from sqlalchemy import Boolean, Date, Float, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from horta.db import Base
from horta.models.traballo import ParteComun

TIPOS_PROBLEMA = ("enfermidade", "praga", "mala_herba", "regulador")


class TratamentoFito(ParteComun, Base):
    __tablename__ = "tratamento_fito"

    id: Mapped[int] = mapped_column(primary_key=True)
    horta_id: Mapped[int] = mapped_column(ForeignKey("horta.id"), index=True)
    data_inicio: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date] = mapped_column(Date)
    hora: Mapped[time | None] = mapped_column(Time, default=None)
    actividade_cuberta: Mapped[str | None] = mapped_column(String(20), default=None)
    eficacia: Mapped[str | None] = mapped_column(String(20), default=None)
```

### Paso 12 — `src/horta/services/caderno.py`

Antes:
```python
                    t.observacions or ""])
```

Despois:
```python
                    t.notas or ""])
```

### Paso 13 — `src/horta/services/caderno.py`

Antes:
```python
                t.observacions or "",
```

Despois:
```python
                t.notas or "",
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (7/9): notas e quen apuntou o tratamento: feito.
