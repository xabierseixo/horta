# Tarefa 075q — Formularios con quen (5/8): toma de mostras

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen colleu a mostra» e horas no formulario da toma de mostras. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/analises.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/analises.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.catalogos_aviso import AVISO_SEN_CATALOGOS
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 2 — `src/horta/ui/pages/analises.py`

Antes:
```python

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar análise").classes("text-h6")
        if not materiais:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
        material = ui.select(materiais, label="Que se analizou").classes("w-full")
        data = campo_data("Data da mostra", date.today().isoformat())
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(40rem, 94vw)"):
        titulo = ui.label("Apuntar análise").classes("text-h6")
        if not materiais:
            ui.label(AVISO_SEN_CATALOGOS).classes("text-warning text-caption")
        material = ui.select(materiais, label="Que se analizou").classes("w-full")
        data = campo_data("Data da mostra", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen colleu a mostra").classes("w-full")
```

### Paso 3 — `src/horta/ui/pages/analises.py`

Antes:
```python
            boletin = ui.input("Nº de boletín").classes("w-full")
```

Despois:
```python
            boletin = ui.input("Nº de boletín").classes("w-full")
            horas = ui.input("Horas de traballo").classes("w-full")
```

### Paso 4 — `src/horta/ui/pages/analises.py`

Antes:
```python
                        if material.value == SOLO else {},
```

Despois:
```python
                        if material.value == SOLO else {},
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value),
```

### Paso 5 — `src/horta/ui/pages/analises.py`

Antes:
```python
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
```

Despois:
```python
        data.value = (a.data_mostraxe if a else date.today()).isoformat()
        persoa.value = (a.persoa_id if a.persoa_id in persoas else None) if a else (
            proposta_quen(horta_id))
        horas.value = f"{a.horas:g}" if a and a.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (5/8): toma de mostras: feito.
