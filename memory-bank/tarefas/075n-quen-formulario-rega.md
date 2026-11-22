# Tarefa 075n — Formularios con quen (2/8): rega

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» e horas no formulario da rega. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/regas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.services.errors import OperacionNonPermitidaError
```

Despois:
```python
from horta.services.errors import OperacionNonPermitidaError
from horta.services.persoas import listar_persoas
```

### Paso 2 — `src/horta/ui/pages/regas.py`

Antes:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 3 — `src/horta/ui/pages/regas.py`

Antes:
```python
                     if "rega" in (v.categoria or "")}
```

Despois:
```python
                     if "rega" in (v.categoria or "")}
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}
```

### Paso 4 — `src/horta/ui/pages/regas.py`

Antes:
```python
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo)")
        sistema = ui.select(sistemas, label="Como se rega").classes("w-full")
        with ui.row().classes("w-full no-wrap items-center"):
            cantidade = ui.input("Auga").classes("col")
            unidade = ui.select(unidades, value="4", label="Unidade").classes("col")
        ui.button("Non sei os litros", icon="calculate", on_click=calculadora.open).props(
            "flat dense")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
```

Despois:
```python
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        superficie = CampoSuperficie("Superficie regada (baleiro = a do cultivo)")
        sistema = ui.select(sistemas, label="Como se rega").classes("w-full")
        with ui.row().classes("w-full no-wrap items-center"):
            cantidade = ui.input("Auga").classes("col")
            unidade = ui.select(unidades, value="4", label="Unidade").classes("col")
        ui.button("Non sei os litros", icon="calculate", on_click=calculadora.open).props(
            "flat dense")
        with ui.expansion("Máis datos").classes("w-full"):
            data_fin = campo_data("Data de fin (se durou máis dun día)")
            horas = ui.input("Horas de traballo").classes("w-full")
```

### Paso 5 — `src/horta/ui/pages/regas.py`

Antes:
```python
                        boas_practicas=list(boas.value or []), notas=notas.value or None)
```

Despois:
```python
                        boas_practicas=list(boas.value or []), notas=notas.value or None,
                        persoa_id=persoa.value, horas=parsear_decimal(horas.value))
```

### Paso 6 — `src/horta/ui/pages/regas.py`

Antes:
```python
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
```

Despois:
```python
        data_fin.value = r.data_fin.isoformat() if r and r.data_fin != r.data_inicio else ""
        persoa.value = (r.persoa_id if r.persoa_id in persoas else None) if r else (
            proposta_quen(horta_id))
        horas.value = f"{r.horas:g}" if r and r.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (2/8): rega: feito.
