# Tarefa 029 — Cultivo completo e colleitas: base de datos

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 028 (migración `e5c9f3b7d2a4`).

## Obxectivo

Primeira parte do deseño `docs/superpowers/specs/2026-10-23-cultivo-e-colleitas-design.md`: campos novos do cultivo (REA), táboa `colleita` e migración que pasa as datas antigas a `data_inicio`/`tipo_inicio` e a cantidade colleitada a unha colleita. Sen cambios na UI nin nos servizos (iso vai noutras tarefas).

## Ficheiros a tocar

- `src/horta/models/colleita.py` (**ficheiro novo**)
- `src/horta/models/cultivo.py`
- `src/horta/models/__init__.py`
- `alembic/versions/f6a1c4e8b9d3_cultivo_completo_e_colleitas.py` (**ficheiro novo**)
- `tests/test_migracion_tratamento_fito.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/models/colleita.py`

Contido completo:

```python
from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from horta.db import Base


class Colleita(Base):
    """Cada colleita dun cultivo (CUE bloque Cosecha) co seu lote. Baixa lóxica."""

    __tablename__ = "colleita"

    id: Mapped[int] = mapped_column(primary_key=True)
    cultivo_id: Mapped[int] = mapped_column(ForeignKey("cultivo.id"), index=True)
    data: Mapped[date] = mapped_column(Date)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade: Mapped[float] = mapped_column(Float)
    unidade: Mapped[str] = mapped_column(String(20))
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    lote: Mapped[str] = mapped_column(String(40))
    albaran_factura: Mapped[str | None] = mapped_column(String(60), default=None)
    destino_colleita: Mapped[str | None] = mapped_column(String(20), default=None)
    destino_restos: Mapped[str | None] = mapped_column(String(20), default=None)
    # Anexo V CUE 11 (colleita): respostas S/N obrigatorias e maquinaria (voluntaria)
    obten_sementes: Mapped[bool] = mapped_column(Boolean, default=False)
    obten_plantas: Mapped[bool] = mapped_column(Boolean, default=False)
    sen_colleita_ambiental: Mapped[bool] = mapped_column(Boolean, default=False)
    restos_no_solo: Mapped[bool] = mapped_column(Boolean, default=False)
    maquina_id: Mapped[int | None] = mapped_column(ForeignKey("maquina.id"), default=None)
    num_repeticions: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_h_ha: Mapped[float | None] = mapped_column(Float, default=None)
    notas: Mapped[str | None] = mapped_column(String(1000), default=None)
    baixa: Mapped[bool] = mapped_column(Boolean, default=False)
    # App do móbil: identificador xerado no móbil (envío sen duplicados)
    uuid: Mapped[str | None] = mapped_column(String(36), unique=True, default=None)
    # Trazabilidade: quen apuntou a colleita
    creado_por: Mapped[int | None] = mapped_column(ForeignKey("usuario.id"), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
```

### Paso 2 — `src/horta/models/cultivo.py`: importar Integer

Antes:
```python
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
```

Despois:
```python
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String
```

### Paso 3 — mesmo ficheiro: campos novos do cultivo

Antes:
```python
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
```

Despois:
```python
    estado: Mapped[str] = mapped_column(String(50), default="planificado")
    # Campos do REA (deseño 2026-10-23-cultivo-e-colleitas). Superficie en hectáreas.
    superficie_ha: Mapped[float | None] = mapped_column(Float, default=None)
    tipo_inicio: Mapped[str | None] = mapped_column(String(12), default=None)
    data_inicio: Mapped[date | None] = mapped_column(Date, default=None)
    data_fin: Mapped[date | None] = mapped_column(Date, default=None)
    causa_baixa: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_cultivo: Mapped[str | None] = mapped_column(String(20), default=None)
    sistema_explotacion: Mapped[str | None] = mapped_column(String(20), default=None)
    destino: Mapped[str | None] = mapped_column(String(20), default=None)
    actividade_agraria: Mapped[str | None] = mapped_column(String(20), default=None)
    certificacion_ecoloxica: Mapped[str | None] = mapped_column(String(20), default=None)
    data_inicio_conversion: Mapped[date | None] = mapped_column(Date, default=None)
    producion_integrada: Mapped[bool] = mapped_column(Boolean, default=False)
    procedencia_material: Mapped[str | None] = mapped_column(String(20), default=None)
    provedor_material: Mapped[str | None] = mapped_column(String(200), default=None)
    lote_material: Mapped[str | None] = mapped_column(String(40), default=None)
    pasaporte_fitosanitario: Mapped[str | None] = mapped_column(String(40), default=None)
    ropveg: Mapped[str | None] = mapped_column(String(20), default=None)
    num_arbores: Mapped[int | None] = mapped_column(Integer, default=None)
    marco_plantacion: Mapped[str | None] = mapped_column(String(20), default=None)
    ano_plantacion: Mapped[int | None] = mapped_column(Integer, default=None)
    unidades_produtivas: Mapped[int | None] = mapped_column(Integer, default=None)
    ciclos_ano: Mapped[int | None] = mapped_column(Integer, default=None)
    duracion_ciclo_dias: Mapped[int | None] = mapped_column(Integer, default=None)
    cultivo_anterior_codigo: Mapped[int | None] = mapped_column(Integer, default=None)
    obxectivo_colleita_kg_ha: Mapped[float | None] = mapped_column(Float, default=None)
    # REA 12 (material vexetal, cobertura, froitos de casca) e CUE 6 (sementeira/plantación)
    tipo_mvr: Mapped[str | None] = mapped_column(String(20), default=None)
    detalle_mvr: Mapped[str | None] = mapped_column(String(20), default=None)
    empresa_semente: Mapped[str | None] = mapped_column(String(20), default=None)
    sementeira_directa: Mapped[bool] = mapped_column(Boolean, default=False)
    tipo_cobertura_solo: Mapped[str | None] = mapped_column(String(20), default=None)
    num_castineiros: Mapped[int | None] = mapped_column(Integer, default=None)
    num_abeleiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_nogueiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_amendoeiras: Mapped[int | None] = mapped_column(Integer, default=None)
    num_outros_froitos_casca: Mapped[int | None] = mapped_column(Integer, default=None)
    data_fin_sementeira: Mapped[date | None] = mapped_column(Date, default=None)
    cantidade_semente_kg: Mapped[float | None] = mapped_column(Float, default=None)
    dose_sementeira_kg_ha: Mapped[float | None] = mapped_column(Float, default=None)
    densidade_plantas_ha: Mapped[float | None] = mapped_column(Float, default=None)
    material_tratado: Mapped[bool] = mapped_column(Boolean, default=False)
    material_adquirido: Mapped[bool] = mapped_column(Boolean, default=False)
    data_adquisicion_material: Mapped[date | None] = mapped_column(Date, default=None)
```

### Paso 4 — `src/horta/models/__init__.py`: rexistrar Colleita

Antes:
```python
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

Despois:
```python
from horta.models.colleita import Colleita
from horta.models.cultivo import Cultivo, Fertilizacion, Tratamento
```

### Paso 5 — mesmo ficheiro

Antes:
```python
    "Tarefa",
```

Despois:
```python
    "Tarefa",
    "Colleita",
```

### Paso 6 — crear o ficheiro `alembic/versions/f6a1c4e8b9d3_cultivo_completo_e_colleitas.py`

Contido completo:

```python
"""cultivo completo e colleitas

Revision ID: f6a1c4e8b9d3
Revises: e5c9f3b7d2a4
Create Date: 2026-10-23 12:00:00

Campos do REA no cultivo, táboa colleita e paso dos datos antigos
(datas de sementeira/plantación e cantidade colleitada).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f6a1c4e8b9d3"
down_revision: Union[str, Sequence[str], None] = "e5c9f3b7d2a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("cultivo") as batch:
        batch.add_column(sa.Column("superficie_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("tipo_inicio", sa.String(12), nullable=True))
        batch.add_column(sa.Column("data_inicio", sa.Date(), nullable=True))
        batch.add_column(sa.Column("data_fin", sa.Date(), nullable=True))
        batch.add_column(sa.Column("causa_baixa", sa.String(20), nullable=True))
        batch.add_column(sa.Column("sistema_cultivo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("sistema_explotacion", sa.String(20), nullable=True))
        batch.add_column(sa.Column("destino", sa.String(20), nullable=True))
        batch.add_column(sa.Column("actividade_agraria", sa.String(20), nullable=True))
        batch.add_column(sa.Column("certificacion_ecoloxica", sa.String(20), nullable=True))
        batch.add_column(sa.Column("data_inicio_conversion", sa.Date(), nullable=True))
        batch.add_column(
            sa.Column("producion_integrada", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("procedencia_material", sa.String(20), nullable=True))
        batch.add_column(sa.Column("provedor_material", sa.String(200), nullable=True))
        batch.add_column(sa.Column("lote_material", sa.String(40), nullable=True))
        batch.add_column(sa.Column("pasaporte_fitosanitario", sa.String(40), nullable=True))
        batch.add_column(sa.Column("ropveg", sa.String(20), nullable=True))
        batch.add_column(sa.Column("num_arbores", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("marco_plantacion", sa.String(20), nullable=True))
        batch.add_column(sa.Column("ano_plantacion", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("unidades_produtivas", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("ciclos_ano", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("duracion_ciclo_dias", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("cultivo_anterior_codigo", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("obxectivo_colleita_kg_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("tipo_mvr", sa.String(20), nullable=True))
        batch.add_column(sa.Column("detalle_mvr", sa.String(20), nullable=True))
        batch.add_column(sa.Column("empresa_semente", sa.String(20), nullable=True))
        batch.add_column(
            sa.Column("sementeira_directa", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("tipo_cobertura_solo", sa.String(20), nullable=True))
        batch.add_column(sa.Column("num_castineiros", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_abeleiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_nogueiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_amendoeiras", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("num_outros_froitos_casca", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("data_fin_sementeira", sa.Date(), nullable=True))
        batch.add_column(sa.Column("cantidade_semente_kg", sa.Float(), nullable=True))
        batch.add_column(sa.Column("dose_sementeira_kg_ha", sa.Float(), nullable=True))
        batch.add_column(sa.Column("densidade_plantas_ha", sa.Float(), nullable=True))
        batch.add_column(
            sa.Column("material_tratado", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(
            sa.Column("material_adquirido", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("data_adquisicion_material", sa.Date(), nullable=True))
    op.create_table(
        "colleita",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cultivo_id", sa.Integer(), sa.ForeignKey("cultivo.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("data_fin", sa.Date(), nullable=True),
        sa.Column("cantidade", sa.Float(), nullable=False),
        sa.Column("unidade", sa.String(20), nullable=False),
        sa.Column("superficie_ha", sa.Float(), nullable=True),
        sa.Column("lote", sa.String(40), nullable=False),
        sa.Column("albaran_factura", sa.String(60), nullable=True),
        sa.Column("destino_colleita", sa.String(20), nullable=True),
        sa.Column("destino_restos", sa.String(20), nullable=True),
        sa.Column("obten_sementes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("obten_plantas", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "sen_colleita_ambiental", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("restos_no_solo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("maquina_id", sa.Integer(), sa.ForeignKey("maquina.id"), nullable=True),
        sa.Column("num_repeticions", sa.Integer(), nullable=True),
        sa.Column("duracion_h_ha", sa.Float(), nullable=True),
        sa.Column("notas", sa.String(1000), nullable=True),
        sa.Column("baixa", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("uuid", sa.String(36), nullable=True, unique=True),
        sa.Column("creado_por", sa.Integer(), sa.ForeignKey("usuario.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_colleita_cultivo_id", "colleita", ["cultivo_id"])
    op.execute(
        "UPDATE cultivo SET tipo_inicio = 'plantacion', data_inicio = data_plantacion "
        "WHERE data_plantacion IS NOT NULL"
    )
    op.execute(
        "UPDATE cultivo SET tipo_inicio = 'sementeira', data_inicio = data_sementeira "
        "WHERE data_inicio IS NULL AND data_sementeira IS NOT NULL"
    )
    op.execute(
        "UPDATE cultivo SET data_fin = data_colleita_real "
        "WHERE estado IN ('colleitado', 'finalizado') AND data_colleita_real IS NOT NULL"
    )
    op.execute(
        "INSERT INTO colleita (cultivo_id, data, cantidade, unidade, lote, baixa, created_at) "
        "SELECT id, COALESCE(data_colleita_real, date(created_at)), cantidade, "
        "COALESCE(unidade, 'kg'), 'MIGRADO-' || id, 0, CURRENT_TIMESTAMP "
        "FROM cultivo WHERE cantidade IS NOT NULL AND cantidade > 0"
    )


def downgrade() -> None:
    op.drop_index("ix_colleita_cultivo_id", table_name="colleita")
    op.drop_table("colleita")
    with op.batch_alter_table("cultivo") as batch:
        batch.drop_column("data_adquisicion_material")
        batch.drop_column("material_adquirido")
        batch.drop_column("material_tratado")
        batch.drop_column("densidade_plantas_ha")
        batch.drop_column("dose_sementeira_kg_ha")
        batch.drop_column("cantidade_semente_kg")
        batch.drop_column("data_fin_sementeira")
        batch.drop_column("num_outros_froitos_casca")
        batch.drop_column("num_amendoeiras")
        batch.drop_column("num_nogueiras")
        batch.drop_column("num_abeleiras")
        batch.drop_column("num_castineiros")
        batch.drop_column("tipo_cobertura_solo")
        batch.drop_column("sementeira_directa")
        batch.drop_column("empresa_semente")
        batch.drop_column("detalle_mvr")
        batch.drop_column("tipo_mvr")
        batch.drop_column("obxectivo_colleita_kg_ha")
        batch.drop_column("cultivo_anterior_codigo")
        batch.drop_column("duracion_ciclo_dias")
        batch.drop_column("ciclos_ano")
        batch.drop_column("unidades_produtivas")
        batch.drop_column("ano_plantacion")
        batch.drop_column("marco_plantacion")
        batch.drop_column("num_arbores")
        batch.drop_column("ropveg")
        batch.drop_column("pasaporte_fitosanitario")
        batch.drop_column("lote_material")
        batch.drop_column("provedor_material")
        batch.drop_column("procedencia_material")
        batch.drop_column("producion_integrada")
        batch.drop_column("data_inicio_conversion")
        batch.drop_column("certificacion_ecoloxica")
        batch.drop_column("actividade_agraria")
        batch.drop_column("destino")
        batch.drop_column("sistema_explotacion")
        batch.drop_column("sistema_cultivo")
        batch.drop_column("causa_baixa")
        batch.drop_column("data_fin")
        batch.drop_column("data_inicio")
        batch.drop_column("tipo_inicio")
        batch.drop_column("superficie_ha")
```

### Paso 7 — `tests/test_migracion_tratamento_fito.py`: engadir ao final do ficheiro

```python
def test_migracion_cultivo_pasa_datas_e_crea_colleita(tmp_path):
    url = f"sqlite:///{tmp_path / 'proba.db'}"
    _alembic(url, "upgrade", "e5c9f3b7d2a4")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO horta (id, nome, uso_profesional, created_at) "
            "VALUES (1, 'Horta', 0, '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO parcela (id, horta_id, nome, estado, created_at) "
            "VALUES (1, 1, 'P1', 'activa', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, estado, data_sementeira, "
            "data_colleita_real, cantidade, unidade, created_at) VALUES (1, 1, 'Pataca', "
            "'colleitado', '2026-03-01', '2026-07-15', 120, 'kg', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO cultivo (id, parcela_id, especie, estado, data_plantacion, "
            "created_at) VALUES (2, 1, 'Leituga', 'plantado', '2026-04-01', '2026-01-01')"
        ))
    _alembic(url, "upgrade", "head")
    with engine.connect() as conn:
        cultivos = conn.execute(text(
            "SELECT id, tipo_inicio, data_inicio, data_fin FROM cultivo ORDER BY id"
        )).all()
        colleitas = conn.execute(text(
            "SELECT cultivo_id, data, cantidade, unidade, lote FROM colleita"
        )).all()
    assert [tuple(map(str, c)) for c in cultivos] == [
        ("1", "sementeira", "2026-03-01", "2026-07-15"),
        ("2", "plantacion", "2026-04-01", "None"),
    ]
    assert [tuple(map(str, c)) for c in colleitas] == [
        ("1", "2026-07-15", "120.0", "kg", "MIGRADO-1"),
    ]
```

## Criterios de aceptación

- `uv run alembic upgrade head` e `uv run alembic downgrade -1` funcionan.
- O test novo da migración pasa e os anteriores tamén.

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
