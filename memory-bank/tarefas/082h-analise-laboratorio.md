# Tarefa 082h — Persoas (9/11): laboratorio das análises

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 082g. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

O laboratorio é unha entidade da lista, co seu NIF. Deseño: `docs/superpowers/specs/2026-10-28-persoas-e-entidades-design.md` (paso 3 de `docs/superpowers/specs/2026-10-28-deseno-global-design.md`)

## Ficheiros a tocar

- `alembic/versions/d0a2c4e6f8b3_analise_laboratorio.py` (**ficheiro novo**)
- `src/horta/models/analise.py`
- `src/horta/services/analises.py`
- `src/horta/ui/pages/analises.py`
- `tests/services/test_analises.py`
- `src/horta/services/caderno.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `alembic/versions/d0a2c4e6f8b3_analise_laboratorio.py`

Contido completo:
```python
"""análises: o laboratorio é unha persoa (entidade co seu NIF)

Revision ID: d0a2c4e6f8b3
Revises: c9f1b3d5e7a2
Create Date: 2026-10-28 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from horta.migracion_persoas import pasar_a_persoas, primeiro


# revision identifiers, used by Alembic.
revision: str = 'd0a2c4e6f8b3'
down_revision: Union[str, Sequence[str], None] = 'c9f1b3d5e7a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("analise") as batch:
        batch.add_column(sa.Column("laboratorio_id", sa.Integer(), nullable=True))
        batch.create_foreign_key("fk_analise_laboratorio_id", "persoa", ["laboratorio_id"], ["id"])
    pasar_a_persoas(
        op.get_bind(), "analise", "laboratorio_id", "laboratorio",
        "SELECT id, horta_id, laboratorio, laboratorio_nif FROM analise",
        nome=lambda f: primeiro(f["laboratorio"], f["laboratorio_nif"]),
        datos=lambda f: {"nif": f["laboratorio_nif"], "tipo": "entidade"})
    with op.batch_alter_table("analise") as batch:
        batch.drop_column("laboratorio")
        batch.drop_column("laboratorio_nif")


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("analise") as batch:
        batch.add_column(sa.Column("laboratorio", sa.String(150), nullable=True))
        batch.add_column(sa.Column("laboratorio_nif", sa.String(9), nullable=True))
    op.get_bind().execute(sa.text(
        "UPDATE analise SET (laboratorio, laboratorio_nif) = (SELECT nome, nif FROM persoa "
        "WHERE persoa.id = analise.laboratorio_id)"))
    with op.batch_alter_table("analise") as batch:
        batch.drop_constraint("fk_analise_laboratorio_id", type_="foreignkey")
        batch.drop_column("laboratorio_id")
```

### Paso 2 — `src/horta/models/analise.py`

Antes:
```python
    laboratorio: Mapped[str | None] = mapped_column(String(150), default=None)
    laboratorio_nif: Mapped[str | None] = mapped_column(String(9), default=None)
```

Despois:
```python
    laboratorio_id: Mapped[int | None] = mapped_column(ForeignKey("persoa.id"), default=None)
```

### Paso 3 — `src/horta/services/analises.py`

Antes:
```python
from horta.services.persoas import comprobar_quen
```

Despois:
```python
from horta.services.persoas import comprobar_quen, persoa_co_papel
```

### Paso 4 — `src/horta/services/analises.py`

Antes:
```python
    laboratorio: str | None = None
    laboratorio_nif: str | None = None
```

Despois:
```python
    # O laboratorio: entidade co papel «laboratorio» (co seu NIF)
    laboratorio_id: int | None = None
```

### Paso 5 — `src/horta/services/analises.py`

Antes:
```python
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
```

Despois:
```python
    comprobar_quen(session, horta_id, datos.persoa_id, datos.horas)
    persoa_co_papel(session, horta_id, datos.laboratorio_id, "laboratorio")
```

### Paso 6 — `src/horta/services/analises.py`

Antes:
```python
    analise.laboratorio = datos.laboratorio or None
    analise.laboratorio_nif = datos.laboratorio_nif or None
```

Despois:
```python
    analise.laboratorio_id = datos.laboratorio_id
```

### Paso 7 — `src/horta/ui/pages/analises.py`

Antes:
```python
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
```

Despois:
```python
from horta.services.persoas import listar_persoas, listar_quen
from horta.ui.accions import executar_accion
from horta.ui.campo_persoa import CampoPersoa
```

### Paso 8 — `src/horta/ui/pages/analises.py`

Antes:
```python
        _ = [(a.tipos, a.substancias) for a in analises]
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
```

Despois:
```python
        _ = [(a.tipos, a.substancias) for a in analises]
        parcelas = {p.id: p.nome for p in session.query(Parcela).filter_by(horta_id=horta_id)}
        cultivos = {c.id: f"{c.especie} — {parcelas[c.parcela_id]}"
                    for c in listar_cultivos(session, actor, horta_id)}
        lotes = {c.id: c.lote for c in listar_colleitas(session, actor, horta_id)}
        materiais = {v.codigo: v.descricion
                     for v in valores_vixentes(session, "material_analizado")}
        tipos = {v.codigo: v.descricion for v in valores_vixentes(session, "tipo_analise")}
        nomes = {p.id: p.nome
                 for p in listar_persoas(session, actor, horta_id, so_activas=False)}
```

### Paso 9 — `src/horta/ui/pages/analises.py`

Antes:
```python
        "laboratorio": a.laboratorio or "",
```

Despois:
```python
        "laboratorio": nomes.get(a.laboratorio_id or 0, ""),
```

### Paso 10 — `src/horta/ui/pages/analises.py`

Antes:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_quen(session, actor, horta_id)}
```

### Paso 11 — `src/horta/ui/pages/analises.py`

Antes:
```python
            laboratorio = ui.input("Laboratorio").classes("w-full")
            nif = ui.input("NIF do laboratorio").classes("w-full")
```

Despois:
```python
            laboratorio = CampoPersoa(horta_id, "laboratorio", "Laboratorio")
```

### Paso 12 — `src/horta/ui/pages/analises.py`

Antes:
```python
                        laboratorio=laboratorio.value or None,
                        laboratorio_nif=nif.value or None, num_boletin=boletin.value or None,
```

Despois:
```python
                        laboratorio_id=laboratorio.value, num_boletin=boletin.value or None,
```

### Paso 13 — `src/horta/ui/pages/analises.py`

Antes:
```python
        laboratorio.value = (a.laboratorio or "") if a else ""
        nif.value = (a.laboratorio_nif or "") if a else ""
```

Despois:
```python
        laboratorio.value = a.laboratorio_id if a else None
```

### Paso 14 — `tests/services/test_analises.py`

Antes:
```python
from horta.services.parcelas import crear_parcela
```

Despois:
```python
from horta.services.parcelas import crear_parcela
from horta.services.persoas import crear_contacto
```

### Paso 15 — `tests/services/test_analises.py`

Antes:
```python
        parcela_id=parcela.id, laboratorio="Lab", solo={"ph": 5.8, "materia_organica": 4.2}),
```

Despois:
```python
        parcela_id=parcela.id,
        laboratorio_id=crear_contacto(session, ana, horta.id, "Lab", "laboratorio").id,
        solo={"ph": 5.8, "materia_organica": 4.2}),
```

### Paso 16 — `src/horta/services/caderno.py`

Antes:
```python
             a.num_boletin or "", a.laboratorio or "",
```

Despois:
```python
             a.num_boletin or "", nome_completo(persoas_por_id.get(a.laboratorio_id or 0)),
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Persoas (9/11): laboratorio das análises: feito.
