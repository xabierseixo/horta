# Tarefa 081g — Parte común (8/9): estado do cultivo calculado

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 081f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O estado do cultivo non se escribe: sae da sementeira, das colleitas e da data de fin. Un cultivo con colleita xa non sae «Planificado». Deseño: `docs/superpowers/specs/2026-10-28-deseno-global-design.md` §5.1 e §3; `docs/como-e-a-app.md` §2.4 (parte común)

## Ficheiros a tocar

- `alembic/versions/b2e4a6c8d0f5_estado_cultivo_calculado.py` (**ficheiro novo**)
- `src/horta/services/cultivos.py`
- `src/horta/ui/pages/cultivos.py`
- `tests/services/test_cultivos.py`
- `tests/models/test_cultivo.py`
- `tests/services/test_fito_consulta.py`
- `src/horta/models/cultivo.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/b2e4a6c8d0f5_estado_cultivo_calculado.py`

Contido completo:
```python
"""o estado do cultivo calcúlase dos seus traballos (services.cultivos.estado_cultivo)

Revision ID: b2e4a6c8d0f5
Revises: a1d3f5b7c9e4
Create Date: 2026-10-28 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2e4a6c8d0f5'
down_revision: Union[str, Sequence[str], None] = 'a1d3f5b7c9e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("estado")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("estado", sa.String(length=50), nullable=False,
                                   server_default="planificado"))
```

### Paso 2 — `src/horta/services/cultivos.py`

Antes:
```python
from typing import Any

```

Despois:
```python
from typing import Any

from sqlalchemy import func
```

### Paso 3 — `src/horta/services/cultivos.py`

Antes:
```python
        "notas",
        "estado",
```

Despois:
```python
        "notas",
```

### Paso 4 — `src/horta/services/cultivos.py`

Antes:
```python
def calcular_estado(cultivo: Cultivo, hoxe: date | None = None) -> str:
    """planificado / en_curso / rematado segundo as datas de inicio e fin."""
    hoxe = hoxe or date.today()
    if cultivo.data_fin is not None and cultivo.data_fin <= hoxe:
        return "rematado"
    if cultivo.data_inicio is not None and cultivo.data_inicio <= hoxe:
        return "en_curso"
    return "planificado"
```

Despois:
```python
def estado_cultivo(cultivo: Cultivo, primeira_colleita: date | None = None,
                   hoxe: date | None = None) -> str:
    """planificado / en_curso / rematado: sae dos traballos do cultivo, non se escribe.

    En curso desde a sementeira ou plantación (data de inicio) ou desde a primeira colleita;
    rematado coa data de fin."""
    hoxe = hoxe or date.today()
    if cultivo.data_fin is not None and cultivo.data_fin <= hoxe:
        return "rematado"
    comezo = min((d for d in (cultivo.data_inicio, primeira_colleita) if d is not None),
                 default=None)
    if comezo is not None and comezo <= hoxe:
        return "en_curso"
    return "planificado"


def estados_cultivos(session: Session, actor: Usuario, horta_id: int,
                     hoxe: date | None = None) -> dict[int, str]:
    """O estado de cada cultivo da explotación (ver estado_cultivo)."""
    cultivos = listar_cultivos(session, actor, horta_id)
    primeiras: dict[int, date] = {
        cultivo_id: data
        for cultivo_id, data in session.query(Colleita.cultivo_id, func.min(Colleita.data))
        .filter(Colleita.cultivo_id.in_([c.id for c in cultivos]), Colleita.baixa.is_(False))
        .group_by(Colleita.cultivo_id)
    }
    return {c.id: estado_cultivo(c, primeiras.get(c.id), hoxe) for c in cultivos}
```

### Paso 5 — `src/horta/services/cultivos.py`

Antes:
```python
    estado = campos.pop("estado", None)
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, **campos)
    cultivo.estado = estado or calcular_estado(cultivo)
```

Despois:
```python
    cultivo = Cultivo(parcela_id=parcela_id, especie=especie, **campos)
```

### Paso 6 — `src/horta/services/cultivos.py`

Antes:
```python
        setattr(cultivo, campo, valor)
    if "estado" not in cambios and {"data_inicio", "data_fin"} & set(cambios):
        cultivo.estado = calcular_estado(cultivo)
```

Despois:
```python
        setattr(cultivo, campo, valor)
```

### Paso 7 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
    eliminar_cultivo,
```

Despois:
```python
    eliminar_cultivo,
    estado_cultivo,
    estados_cultivos,
```

### Paso 8 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
```

Despois:
```python
        colleitas = listar_colleitas(session, actor, horta_id)
        estados = estados_cultivos(session, actor, horta_id)
```

### Paso 9 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            "estado": _ESTADOS.get(c.estado, c.estado),
```

Despois:
```python
            "estado": _ESTADOS[estados[c.id]],
```

### Paso 10 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                              if c.parcela_id == p.id and c.estado != "rematado")
```

Despois:
```python
                              if c.parcela_id == p.id and estado_cultivo(c) != "rematado")
```

### Paso 11 — `tests/services/test_cultivos.py`

Antes:
```python
from horta.services.cultivos import (
    actualizar_cultivo,
    calcular_estado,
    crear_cultivo,
    eliminar_cultivo,
```

Despois:
```python
from horta.services.colleitas import DatosColleita, crear_colleita, dar_de_baixa_colleita
from horta.services.cultivos import (
    actualizar_cultivo,
    crear_cultivo,
    eliminar_cultivo,
    estado_cultivo,
    estados_cultivos,
```

### Paso 12 — `tests/services/test_cultivos.py`

Antes:
```python
    assert cultivo.estado == "planificado"
```

Despois:
```python
    assert estado_cultivo(cultivo) == "planificado"
```

### Paso 13 — `tests/services/test_cultivos.py`

Antes:
```python
    actualizado = actualizar_cultivo(session, ana, cultivo, estado="sementado")
    assert actualizado.estado == "sementado"
```

Despois:
```python
    actualizado = actualizar_cultivo(session, ana, cultivo, notas="regar ben")
    assert actualizado.notas == "regar ben"
```

### Paso 14 — `tests/services/test_cultivos.py`

Antes:
```python
        actualizar_cultivo(session, carlos, cultivo, estado="sementado")
```

Despois:
```python
        actualizar_cultivo(session, carlos, cultivo, notas="regar ben")
```

### Paso 15 — `tests/services/test_cultivos.py`

Antes:
```python
    assert cultivo.estado == "en_curso"
    actualizar_cultivo(session, ana, cultivo, data_fin=date(2026, 7, 1))
    assert cultivo.estado == "rematado"
    assert calcular_estado(cultivo, hoxe=date(2026, 6, 1)) == "en_curso"
```

Despois:
```python
    assert estado_cultivo(cultivo, hoxe=date(2026, 2, 1)) == "planificado"
    assert estado_cultivo(cultivo, hoxe=date(2026, 6, 1)) == "en_curso"
    actualizar_cultivo(session, ana, cultivo, data_fin=date(2026, 7, 1))
    assert estado_cultivo(cultivo, hoxe=date(2026, 7, 2)) == "rematado"


def test_estado_en_curso_desde_a_primeira_colleita(session):
    """Un cultivo sen data de inicio pero con colleita xa non está planificado."""
    ana, parcela = _parcela_de_proba(session)
    cultivo = crear_cultivo(session, ana, parcela.id, "Pataca")
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "planificado"
    colleita = crear_colleita(session, ana, DatosColleita(
        cultivo_id=cultivo.id, data=date(2026, 9, 1), cantidade=120, unidade="kg", lote="",
        persoa_id=1), hoxe=date(2026, 10, 1))
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "en_curso"
    dar_de_baixa_colleita(session, ana, colleita)
    assert estados_cultivos(session, ana, parcela.horta_id)[cultivo.id] == "planificado"
```

### Paso 16 — `tests/models/test_cultivo.py`

Antes:
```python
    assert atopado.parcela_id == parcela.id
    assert atopado.estado == "planificado"
```

Despois:
```python
    assert atopado.parcela_id == parcela.id
```

### Paso 17 — `tests/services/test_fito_consulta.py`

Antes:
```python
    cultivo = Cultivo(parcela_id=parcela.id, especie="Pataca", estado="en_curso",
```

Despois:
```python
    cultivo = Cultivo(parcela_id=parcela.id, especie="Pataca",
```

### Paso 18 — `src/horta/models/cultivo.py`

Antes:
```python
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
```

Despois:
```python
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Parte común (8/9): estado do cultivo calculado: feito.
