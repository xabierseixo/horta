# Tarefa 075m — Formularios con quen (1/8): labor

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075l. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» á vista no formulario do labor, propondo quen fixo o último traballo; horas en «Máis datos». Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/quen.py` (**ficheiro novo**)
- `src/horta/ui/pages/labores.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/quen.py`

Contido completo:
```python
"""«Quen o fixo» nos formularios de traballo: todo traballo o fai unha persoa do equipo."""

from __future__ import annotations

from horta.db import get_session
from horta.services.diario import ultima_persoa
from horta.ui.sesion import usuario_actual


def proposta_quen(horta_id: int) -> int | None:
    """Quen fixo o último traballo, para propoñelo ao apuntar o seguinte."""
    with get_session() as session:
        actor = usuario_actual(session)
        return ultima_persoa(session, actor, horta_id) if actor else None
```

### Paso 2 — `src/horta/ui/pages/labores.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 3 — `src/horta/ui/pages/labores.py`

Antes:
```python
        restos_desbroce = ui.checkbox("Os restos do desbroce quedaron no chan")
        restos_poda = ui.checkbox("Os restos da poda quedaron no chan")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            superficie = CampoSuperficie("Superficie (baleiro = a do cultivo)")
            cobertura = ui.select(coberturas, label="Cobertura do solo (baleiro = a do cultivo)",
                                  clearable=True).classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                repeticions = ui.input("Nº de pasadas").classes("col")
                horas = ui.input("Horas de cada pasada").classes("col")
            persoa = ui.select(persoas, label="Quen o fixo", clearable=True).classes("w-full")
```

Despois:
```python
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        restos_desbroce = ui.checkbox("Os restos do desbroce quedaron no chan")
        restos_poda = ui.checkbox("Os restos da poda quedaron no chan")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas_traballo = ui.input("Horas de traballo").classes("w-full")
            superficie = CampoSuperficie("Superficie (baleiro = a do cultivo)")
            cobertura = ui.select(coberturas, label="Cobertura do solo (baleiro = a do cultivo)",
                                  clearable=True).classes("w-full")
            maquina = ui.select(maquinas, label="Máquina", clearable=True).classes("w-full")
            with ui.row().classes("w-full no-wrap"):
                repeticions = ui.input("Nº de pasadas").classes("col")
                horas = ui.input("Horas de cada pasada").classes("col")
```

### Paso 4 — `src/horta/ui/pages/labores.py`

Antes:
```python
                        notas=notas.value or None)
```

Despois:
```python
                        horas=parsear_decimal(horas_traballo.value), notas=notas.value or None)
```

### Paso 5 — `src/horta/ui/pages/labores.py`

Antes:
```python
        persoa.value = lab.persoa_id if lab and lab.persoa_id in persoas else None
```

Despois:
```python
        persoa.value = (lab.persoa_id if lab.persoa_id in persoas else None) if lab else (
            proposta_quen(horta_id))
        horas_traballo.value = f"{lab.horas:g}" if lab and lab.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (1/8): labor: feito.
