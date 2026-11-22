# Tarefa 075v — Informes: traballos sen quen o fixo

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075u. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

En Informes, a todas as explotacións, cantos traballos de antes non teñen quen o fixo, coa ligazón para completalos. Probado no navegador (escritorio e móbil) o 2026-10-27. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/informes.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/informes.py`

Antes:
```python
"""Informes: o que sae do traballo apuntado. Hoxe, o caderno de explotación e o que lle falta."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.faltas_caderno import faltas_caderno
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.layout import url_seccion
```

Despois:
```python
"""Informes: o que sae do traballo apuntado. Hoxe, o caderno de explotación, o que lle falta e
os traballos sen quen o fixo."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from horta.db import get_session
from horta.services.diario import TIPOS, sen_quen
from horta.services.faltas_caderno import faltas_caderno
from horta.ui.descarga_caderno import boton_caderno
from horta.ui.layout import url_seccion
from horta.ui.pages.diario import SECCION_DO_TIPO
```

### Paso 2 — `src/horta/ui/pages/informes.py`

Antes:
```python
        boton_caderno(horta_id)
```

Despois:
```python
        boton_caderno(horta_id)
    _sen_quen(horta_id)
```

### Paso 3 — `src/horta/ui/pages/informes.py`

Antes:
```python
                ui.link("Ver", url_seccion(horta_id, _SECCION_DA_FALTA[falta.traballo]))
```

Despois:
```python
                ui.link("Ver", url_seccion(horta_id, _SECCION_DA_FALTA[falta.traballo]))


def _sen_quen(horta_id: int) -> None:
    """Os traballos apuntados antes de pedir quen o fixo: complétanse, non se inventan."""
    with get_session() as session:
        actor = usuario_actual(session)
        contas = sen_quen(session, actor, horta_id) if actor else {}
    if not contas:
        return
    with ui.column().classes("tarxeta w-full gap-2 q-pa-md q-mt-md"):
        ui.label("Traballos sen quen o fixo").classes("text-subtitle1 text-weight-bold")
        ui.label("Apuntáronse antes de pedilo. Ábreos e indica quen o fixo.").classes(
            "texto-suave")
        for tipo, cantos in contas.items():
            with ui.row().classes("items-center gap-2"):
                ui.icon("person_off").classes("text-warning")
                ui.label(f"{TIPOS[tipo]}: {cantos}")
                ui.link("Ver", url_seccion(horta_id, SECCION_DO_TIPO[tipo]))
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Informes: traballos sen quen o fixo: feito.
