# Tarefa 027 — Superficies en hectáreas, escritas en m² ou ha

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 026.

## Obxectivo

O CUE pide as superficies en hectáreas, pero parcelas e fertilizacións gardábanas en m². Decisión do usuario (2026-10-23): a app garda **sempre hectáreas**, e cada campo de superficie ten un selector para escribir en **m² ou ha**. As táboas amosan m² se é menos dunha hectárea. Unha migración pasa os datos existentes de m² a ha.

## Ficheiros a tocar

- `src/horta/ui/superficie.py` (**ficheiro novo**)
- `alembic/versions/d4b8e2a6c1f3_superficies_en_hectareas.py` (**ficheiro novo**)
- `tests/ui/test_superficie.py` (**ficheiro novo**)
- `src/horta/models/parcela.py`
- `src/horta/models/cultivo.py`
- `src/horta/services/tratamentos_fito.py`
- `tests/services/test_tratamentos_fito.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/superficie.py`

Contido completo:

```python
"""Superficies: a app garda hectáreas; o usuario escribe en m² ou ha."""

from __future__ import annotations

from nicegui import ui

M2_POR_HA = 10_000
UNIDADES_SUPERFICIE = ("m²", "ha")


def a_hectareas(valor: float | None, unidade: str) -> float | None:
    """Converte o valor escrito (en m² ou ha) a hectáreas."""
    if valor is None:
        return None
    if unidade == "m²":
        return round(float(valor) / M2_POR_HA, 6)
    return round(float(valor), 6)


def desde_hectareas(ha: float | None, unidade: str) -> float | None:
    """Converte hectáreas á unidade amosada no campo."""
    if ha is None:
        return None
    if unidade == "m²":
        return round(ha * M2_POR_HA, 2)
    return round(ha, 6)


def formatar_superficie(ha: float | None) -> str:
    """Texto para táboas: menos dunha hectárea en m², o resto en ha."""
    if ha is None:
        return ""
    if ha < 1:
        return f"{ha * M2_POR_HA:.0f} m²"
    return f"{ha:.2f} ha".replace(".", ",")


class CampoSuperficie:
    """Número + selector m²/ha. A app garda sempre hectáreas (o CUE pide ha)."""

    def __init__(self, etiqueta: str, unidade: str = "m²") -> None:
        self._unidade_anterior = unidade
        with ui.row().classes("w-full no-wrap items-end gap-2"):
            self.numero = ui.number(etiqueta, min=0).classes("col-grow")
            self.unidade = ui.select(
                list(UNIDADES_SUPERFICIE), value=unidade, label="Unidade",
                on_change=self._cambiar_unidade,
            ).classes("w-24")

    @property
    def ha(self) -> float | None:
        return a_hectareas(self.numero.value, self.unidade.value)

    def establecer(self, ha: float | None) -> None:
        unidade = "ha" if ha is not None and ha >= 1 else "m²"
        self._unidade_anterior = unidade
        self.unidade.value = unidade
        self.numero.value = desde_hectareas(ha, unidade)

    def _cambiar_unidade(self) -> None:
        ha = a_hectareas(self.numero.value, self._unidade_anterior)
        self._unidade_anterior = self.unidade.value
        self.numero.value = desde_hectareas(ha, self.unidade.value)
```

### Paso 2 — crear o ficheiro `alembic/versions/d4b8e2a6c1f3_superficies_en_hectareas.py`

Contido completo:

```python
"""superficies en hectareas

Revision ID: d4b8e2a6c1f3
Revises: c3a9e1f0b7d2
Create Date: 2026-10-23 10:00:00

Parcelas e fertilizacións gardaban a superficie en m²; o CUE pide hectáreas.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "d4b8e2a6c1f3"
down_revision: Union[str, Sequence[str], None] = "c3a9e1f0b7d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE parcela SET superficie = superficie / 10000.0 WHERE superficie IS NOT NULL")
    op.execute(
        "UPDATE fertilizacion SET superficie = superficie / 10000.0 WHERE superficie IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("UPDATE parcela SET superficie = superficie * 10000.0 WHERE superficie IS NOT NULL")
    op.execute(
        "UPDATE fertilizacion SET superficie = superficie * 10000.0 WHERE superficie IS NOT NULL"
    )
```

### Paso 3 — crear o ficheiro `tests/ui/test_superficie.py`

Contido completo:

```python
import pytest

from horta.ui.superficie import a_hectareas, desde_hectareas, formatar_superficie


def test_m2_a_hectareas():
    assert a_hectareas(250, "m²") == 0.025


def test_ha_queda_igual():
    assert a_hectareas(1.5, "ha") == 1.5


def test_hectareas_a_m2():
    assert desde_hectareas(0.025, "m²") == 250


@pytest.mark.parametrize("funcion", [a_hectareas, desde_hectareas])
def test_baleiro_queda_baleiro(funcion):
    assert funcion(None, "m²") is None


def test_formatar_superficie():
    assert formatar_superficie(0.025) == "250 m²"
    assert formatar_superficie(1.5) == "1,50 ha"
    assert formatar_superficie(None) == ""
```

### Paso 4 — `src/horta/models/parcela.py`

Antes:
```python
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    superficie: Mapped[float | None] = mapped_column(Float, default=None)  # hectáreas
```

### Paso 5 — `src/horta/models/cultivo.py` (fertilización)

Antes:
```python
    superficie: Mapped[float | None] = mapped_column(Float, default=None)
```

Despois:
```python
    superficie: Mapped[float | None] = mapped_column(Float, default=None)  # hectáreas
```

### Paso 6 — `src/horta/services/tratamentos_fito.py`: a parcela xa está en ha

Antes:
```python
            if parcela.superficie and linha.superficie_ha > parcela.superficie / 10000:
```

Despois:
```python
            if parcela.superficie and linha.superficie_ha > parcela.superficie:
```

### Paso 7 — `tests/services/test_tratamentos_fito.py`

Antes:
```python
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=2000.0)
```

Despois:
```python
    parcela = crear_parcela(session, ana, horta.id, "P1", superficie=0.2)
```

### Paso 8 — mesmo ficheiro

Antes:
```python
    ana, horta, _, cultivo, xan, maquina = _escenario(session)  # parcela de 2000 m² = 0,2 ha
```

Despois:
```python
    ana, horta, _, cultivo, xan, maquina = _escenario(session)  # parcela de 0,2 ha
```

## Comprobacións

```bash
uv run ruff check src tests
uv run mypy src
uv run pytest -q
```

## Resultado

(Enche isto ao rematar: que fixeches, se pasaron as comprobacións, commit.)
