# Tarefa 035 — Equipo: datos e regras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 034 (migración `f6a1c4e8b9d3`).

## Obxectivo

Base de Equipo segundo `docs/superpowers/specs/2026-10-23-equipo-design.md`: campos novos de `persoa` (conta, funcións, contacto, vínculo, horas/ano, formación, colectivo), migración que mete os membros actuais no equipo, servizo `equipo.py` (dar e quitar acceso, UTA) e o creador dunha explotación entra no equipo. Sen cambios na pantalla (tarefa 036).

## Ficheiros a tocar

- `src/horta/models/persoa.py`
- `alembic/versions/a7d2e5f8c3b1_equipo.py` (**ficheiro novo**)
- `src/horta/services/persoas.py`
- `src/horta/services/equipo.py` (**ficheiro novo**)
- `src/horta/services/hortas.py`
- `tests/services/test_equipo.py` (**ficheiro novo**)
- `tests/services/test_persoas.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/models/persoa.py`: campos novos

Antes:
```python
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
```

Despois:
```python
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    # Equipo (deseño 2026-10-23-equipo): conta, funcións e datos de emprego (UTA, AGADER)
    usuario_id: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    e_titular: Mapped[bool] = mapped_column(Boolean, default=False)
    e_traballador: Mapped[bool] = mapped_column(Boolean, default=False)
    telefono: Mapped[str | None] = mapped_column(String(30), default=None)
    email: Mapped[str | None] = mapped_column(String(255), default=None)
    vinculo: Mapped[str | None] = mapped_column(String(20), default=None)
    horas_ano: Mapped[float | None] = mapped_column(Float, default=None)
    formacion_agraria: Mapped[str | None] = mapped_column(String(200), default=None)
    xenero: Mapped[str | None] = mapped_column(String(10), default=None)
    data_nacemento: Mapped[date | None] = mapped_column(Date, default=None)
    discapacidade: Mapped[bool] = mapped_column(Boolean, default=False)
```

### Paso 2 — mesmo ficheiro: importar Float

Antes:
```python
from sqlalchemy import Boolean, Date, Enum, ForeignKey, String
```

Despois:
```python
from sqlalchemy import Boolean, Date, Enum, Float, ForeignKey, String
```

### Paso 3 — crear o ficheiro `alembic/versions/a7d2e5f8c3b1_equipo.py`

Contido completo:

```python
"""equipo: persoas con conta, funcions e datos de emprego

Revision ID: a7d2e5f8c3b1
Revises: f6a1c4e8b9d3
Create Date: 2026-10-23 13:00:00

Cada membro actual pasa a ser unha persoa do equipo ligada á súa conta.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7d2e5f8c3b1"
down_revision: Union[str, Sequence[str], None] = "f6a1c4e8b9d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("persoa") as batch:
        batch.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("e_titular", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column("e_traballador", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("telefono", sa.String(30), nullable=True))
        batch.add_column(sa.Column("email", sa.String(255), nullable=True))
        batch.add_column(sa.Column("vinculo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("horas_ano", sa.Float(), nullable=True))
        batch.add_column(sa.Column("formacion_agraria", sa.String(200), nullable=True))
        batch.add_column(sa.Column("xenero", sa.String(10), nullable=True))
        batch.add_column(sa.Column("data_nacemento", sa.Date(), nullable=True))
        batch.add_column(
            sa.Column("discapacidade", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.create_foreign_key("fk_persoa_usuario", "usuario", ["usuario_id"], ["id"])
    op.execute(
        "INSERT INTO persoa (horta_id, nome, usuario_id, email, e_aplicador, e_asesor, activa, "
        "e_titular, e_traballador, discapacidade) "
        "SELECT m.horta_id, u.nome, u.id, u.email, 0, 0, 1, 0, 0, 0 "
        "FROM horta_membro m JOIN usuario u ON u.id = m.usuario_id "
        "WHERE NOT EXISTS (SELECT 1 FROM persoa p "
        "WHERE p.horta_id = m.horta_id AND p.usuario_id = m.usuario_id)"
    )


def downgrade() -> None:
    op.execute("DELETE FROM persoa WHERE usuario_id IS NOT NULL AND e_aplicador = 0 "
               "AND e_asesor = 0")
    with op.batch_alter_table("persoa") as batch:
        batch.drop_constraint("fk_persoa_usuario", type_="foreignkey")
        for columna in ("discapacidade", "data_nacemento", "xenero", "formacion_agraria",
                        "horas_ano", "vinculo", "email", "telefono", "e_traballador",
                        "e_titular", "usuario_id"):
            batch.drop_column(columna)
```

### Paso 4 — `src/horta/services/persoas.py`: campos editables novos

Antes:
```python
    {"nome", "apelidos", "nif", "e_aplicador", "e_asesor", "ropo_numero", "ropo_tipo_carne",
     "ropo_caducidade", "regfer_numero", "activa"}
```

Despois:
```python
    {"nome", "apelidos", "nif", "e_aplicador", "e_asesor", "ropo_numero", "ropo_tipo_carne",
     "ropo_caducidade", "regfer_numero", "activa", "e_titular", "e_traballador", "telefono",
     "email", "vinculo", "horas_ano", "formacion_agraria", "xenero", "data_nacemento",
     "discapacidade"}
```

### Paso 5 — mesmo ficheiro: validacións novas

Antes:
```python
    if datos.get("e_asesor") and not datos.get("ropo_numero"):
        raise OperacionNonPermitidaError("Un asesor precisa o nº ROPO")
```

Despois:
```python
    if datos.get("e_asesor") and not datos.get("ropo_numero"):
        raise OperacionNonPermitidaError("Un asesor precisa o nº ROPO")
    if datos.get("vinculo") not in (None, *VINCULOS):
        raise OperacionNonPermitidaError(f"Vínculo non válido: {datos['vinculo']}")
    if datos.get("horas_ano") is not None and not 0 <= datos["horas_ano"] <= 4000:
        raise OperacionNonPermitidaError("As horas ao ano teñen que estar entre 0 e 4.000")
    if datos.get("xenero") not in (None, *XENEROS):
        raise OperacionNonPermitidaError(f"Xénero non válido: {datos['xenero']}")
    if datos.get("data_nacemento") is not None and datos["data_nacemento"] > date.today():
        raise OperacionNonPermitidaError("A data de nacemento non pode ser futura")
```

### Paso 6 — mesmo ficheiro: valores permitidos

Antes:
```python
def _normalizar_e_validar(datos: dict[str, Any]) -> None:
```

Despois:
```python
VINCULOS = ("titular", "familiar", "asalariado", "socio", "externo")
XENEROS = ("muller", "home", "outro")


def _normalizar_e_validar(datos: dict[str, Any]) -> None:
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
