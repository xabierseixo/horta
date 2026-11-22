# Tarefa 081e — Parte común (6/9): quen aplicou o abono

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081d. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Quen aplicou o abono gárdase como en todos os traballos (persoa_id). Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `alembic/versions/f0c2e4a6b8d3_abonado_persoa.py` (**ficheiro novo**)
- `src/horta/services/abonados.py`
- `src/horta/ui/pages/abonados.py`
- `src/horta/services/diario.py`
- `tests/services/test_abonados.py`
- `tests/services/test_apuntar_minimo.py`
- `tests/services/test_quen.py`
- `src/horta/models/abonado.py`
- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/f0c2e4a6b8d3_abonado_persoa.py`

Contido completo:
```python
"""parte común: quen aplicou o abono chámase persoa_id, como nos outros traballos

Revision ID: f0c2e4a6b8d3
Revises: e9b1d3f5a7c2
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f0c2e4a6b8d3'
down_revision: Union[str, Sequence[str], None] = 'e9b1d3f5a7c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.alter_column("aplicador_persoa_id", new_column_name="persoa_id")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("abonado") as batch:
        batch.alter_column("persoa_id", new_column_name="aplicador_persoa_id")
```

### Paso 2 — `src/horta/services/abonados.py`

Antes:
```python
    aplicador_persoa_id: int | None = None
```

Despois:
```python
    persoa_id: int | None = None
```

### Paso 3 — `src/horta/services/abonados.py`

Antes:
```python
    comprobar_quen(session, horta_id, datos.aplicador_persoa_id, datos.horas,
```

Despois:
```python
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas,
```

### Paso 4 — `src/horta/services/abonados.py`

Antes:
```python
    abonado.aplicador_persoa_id = datos.aplicador_persoa_id
```

Despois:
```python
    abonado.persoa_id = datos.persoa_id
```

### Paso 5 — `src/horta/ui/pages/abonados.py`

Antes:
```python
                        albaran_factura=albaran.value or None, aplicador_persoa_id=aplicador.value,
```

Despois:
```python
                        albaran_factura=albaran.value or None, persoa_id=aplicador.value,
```

### Paso 6 — `src/horta/ui/pages/abonados.py`

Antes:
```python
        aplicador.value = (a.aplicador_persoa_id if a.aplicador_persoa_id in persoas
```

Despois:
```python
        aplicador.value = (a.persoa_id if a.persoa_id in persoas
```

### Paso 7 — `src/horta/services/diario.py`

Antes:
```python
        quen = _quen(a.aplicador_persoa_id)
```

Despois:
```python
        quen = _quen(a.persoa_id)
```

### Paso 8 — `tests/services/test_abonados.py`

Antes:
```python
    return DatosAbonado(**{"aplicador_persoa_id": QUEN, **base})
```

Despois:
```python
    return DatosAbonado(**{"persoa_id": QUEN, **base})
```

### Paso 9 — `tests/services/test_apuntar_minimo.py`

Antes:
```python
    abonado = crear_abonado(session, ana, DatosAbonado(aplicador_persoa_id=QUEN,
```

Despois:
```python
    abonado = crear_abonado(session, ana, DatosAbonado(persoa_id=QUEN,
```

### Paso 10 — `tests/services/test_quen.py`

Antes:
```python
        aplicador_persoa_id=persoa_id, horas=horas), hoxe=HOXE)
```

Despois:
```python
        persoa_id=persoa_id, horas=horas), hoxe=HOXE)
```

### Paso 11 — `tests/services/test_quen.py`

Antes:
```python
    persoa_id = rexistro.aplicador_persoa_id if tipo == "abonado" else rexistro.persoa_id
    assert persoa_id == ana_persoa.id and rexistro.horas == 1.5
```

Despois:
```python
    assert rexistro.persoa_id == ana_persoa.id and rexistro.horas == 1.5
```

### Paso 12 — `tests/services/test_quen.py`

Antes:
```python
    assert abonado.aplicador_persoa_id is None
```

Despois:
```python
    assert abonado.persoa_id is None
```

### Paso 13 — `src/horta/models/abonado.py`

Antes:
```python
from horta.models.traballo import ConMaquina, ParteComun
```

Despois:
```python
from horta.models.traballo import ConMaquina, FeitoPor, ParteComun
```

### Paso 14 — `src/horta/models/abonado.py`

Antes:
```python
class Abonado(ParteComun, ConMaquina, Base):
```

Despois:
```python
class Abonado(ParteComun, FeitoPor, ConMaquina, Base):
```

### Paso 15 — `src/horta/models/abonado.py`

Antes:
```python
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
    aplicador_persoa_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    horas: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    albaran_factura: Mapped[str | None] = mapped_column(String(50), default=None)
```

### Paso 16 — `src/horta/services/caderno.py`

Antes:
```python
        persoa = session.get(Persoa, ab.aplicador_persoa_id) if ab.aplicador_persoa_id else None
```

Despois:
```python
        persoa = session.get(Persoa, ab.persoa_id) if ab.persoa_id else None
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (6/9): quen aplicou o abono: feito.
