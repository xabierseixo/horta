# Tarefa 082f — Persoas (7/11): provedor da semente ou planta

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O provedor da semente ou planta (co seu ROPVEG) escóllese da lista de persoas. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/b8e0a2c4d6f1_cultivo_provedor_material.py` (**ficheiro novo**)
- `src/horta/models/cultivo.py`
- `src/horta/services/cultivos.py`
- `src/horta/ui/pages/cultivos.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/b8e0a2c4d6f1_cultivo_provedor_material.py`

Contido completo:
```python
"""cultivo: o provedor da semente ou planta é unha persoa, co seu ROPVEG

Revision ID: b8e0a2c4d6f1
Revises: a7d9f1b3c5e0
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'b8e0a2c4d6f1'
down_revision: Union[str, Sequence[str], None] = 'a7d9f1b3c5e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("provedor_material_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_cultivo_provedor_material_id", "persoa", ["provedor_material_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "cultivo", "provedor_material_id", "provedor",
        "SELECT c.id, p.horta_id, c.provedor_material, c.ropveg FROM cultivo c "
        "JOIN parcela p ON p.id = c.parcela_id",
        nome=lambda f: primeiro(f["provedor_material"],
                                f["ropveg"] and f"Provedor (ROPVEG {f['ropveg']})"),
        datos=lambda f: {"ropveg": f["ropveg"]})
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("provedor_material")
        batch.drop_column("ropveg")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("provedor_material", sa.String(200), nullable=True))
        batch.add_column(sa.Column("ropveg", sa.String(20), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE cultivo SET (provedor_material, ropveg) = (SELECT nome, ropveg FROM persoa "
        "WHERE persoa.id = cultivo.provedor_material_id)"))
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_constraint("fk_cultivo_provedor_material_id", type_="foreignkey")
        batch.drop_column("provedor_material_id")
```

### Paso 2 — `src/horta/models/cultivo.py`

Antes:
```python
    provedor_material: Mapped[str | None] = mapped_column(String(200), default=None)
    lote_material: Mapped[str | None] = mapped_column(String(40), default=None)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
    ropveg: Mapped[str | None] = mapped_column(String(20), default=None)
```

Despois:
```python
    provedor_material_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
    lote_material: Mapped[str | None] = mapped_column(String(40), default=None)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
```

### Paso 3 — `src/horta/services/cultivos.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

### Paso 4 — `src/horta/services/cultivos.py`

Antes:
```python
        "provedor_material",
        "lote_material",
        "pasaporte_fitosanitario",
        "ropveg",
```

Despois:
```python
        "provedor_material_id",
        "lote_material",
        "pasaporte_fitosanitario",
```

### Paso 5 — `src/horta/services/cultivos.py`

Antes:
```python
                   campos.get("sementeira_horas"), obrigatoria=False)
```

Despois:
```python
                   campos.get("sementeira_horas"), obrigatoria=False)
    persoa_co_papel(session, horta_id, campos.get("provedor_material_id"), "provedor")
```

### Paso 6 — `src/horta/services/cultivos.py`

Antes:
```python
                   cambios.get("sementeira_horas"), obrigatoria=False)
```

Despois:
```python
                   cambios.get("sementeira_horas"), obrigatoria=False)
    persoa_co_papel(session, horta_id, cambios.get("provedor_material_id"), "provedor")
```

### Paso 7 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.services.persoas import listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

### Paso 8 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 9 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
            provedor = ui.input("Provedor").classes("w-full")
            lote_material = ui.input("Lote da semente ou planta").classes("w-full")
            pasaporte = ui.input("Pasaporte fitosanitario").classes("w-full")
            ropveg = ui.input("Nº ROPVEG do provedor").classes("w-full")
```

Despois:
```python
            # O provedor e o seu ROPVEG: ficha en Persoas
            provedor = CampoPersoa(horta_id, "provedor", "Provedor")
            lote_material = ui.input("Lote da semente ou planta").classes("w-full")
            pasaporte = ui.input("Pasaporte fitosanitario").classes("w-full")
```

### Paso 10 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                provedor_material=provedor.value or None,
                lote_material=lote_material.value or None,
                pasaporte_fitosanitario=pasaporte.value or None,
                ropveg=ropveg.value or None,
```

Despois:
```python
                provedor_material_id=provedor.value,
                lote_material=lote_material.value or None,
                pasaporte_fitosanitario=pasaporte.value or None,
```

### Paso 11 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                    provedor, lote_material, pasaporte, ropveg, num_arbores, marco,
```

Despois:
```python
                    lote_material, pasaporte, num_arbores, marco,
```

### Paso 12 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
                selector.value = None
```

Despois:
```python
                selector.value = None
            provedor.value = None
```

### Paso 13 — `src/horta/ui/pages/cultivos.py`

Antes:
```python
        provedor.value = _texto(c.provedor_material)
        lote_material.value = _texto(c.lote_material)
        pasaporte.value = _texto(c.pasaporte_fitosanitario)
        ropveg.value = _texto(c.ropveg)
```

Despois:
```python
        provedor.value = c.provedor_material_id
        lote_material.value = _texto(c.lote_material)
        pasaporte.value = _texto(c.pasaporte_fitosanitario)
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (7/11): provedor da semente ou planta: feito.
