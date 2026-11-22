# Tarefa 075r — Formularios con quen (6/8): colleita

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 075m. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

«Quen o fixo» e horas no formulario da colleita. Deseño: `docs/superpowers/specs/2026-10-27-quen-e-horas-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
```

Despois:
```python
from horta.services.persoas import listar_persoas
from horta.ui.accions import executar_accion
from horta.ui.campos import campo_data
from horta.ui.confirmacion import confirmar_eliminacion
from horta.ui.numeros import parsear_data, parsear_decimal
from horta.ui.quen import proposta_quen
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`

Antes:
```python

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("Apuntar colleita").classes("text-h6")
        cultivo = ui.select(nome_cultivo, label="Cultivo", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
        lote = ui.input("Lote").classes("w-full")
        albaran = ui.input("Nº de albarán ou factura (opcional)").classes("w-full")
        superficie = CampoSuperficie("Superficie colleitada (baleiro = a do cultivo)")
        data_fin = campo_data("Data de fin (se durou máis dun día)")
```

Despois:
```python
        persoas = {p.id: p.nome for p in listar_persoas(session, actor, horta_id)}

    editando: dict[str, int | None] = {"id": None}

    with ui.dialog() as dialogo, ui.card().style("width: min(32rem, 94vw)"):
        titulo = ui.label("Apuntar colleita").classes("text-h6")
        cultivo = ui.select(nome_cultivo, label="Cultivo", with_input=True).classes("w-full")
        data = campo_data("Data", date.today().isoformat())
        persoa = ui.select(persoas, label="Quen o fixo").classes("w-full")
        with ui.row().classes("w-full no-wrap gap-2"):
            cantidade = ui.input("Cantidade").classes("col-grow")
            unidade = ui.select(list(UNIDADES_COLLEITA), value="kg", label="Unidade").classes(
                "w-28")
        lote = ui.input("Lote").classes("w-full")
        albaran = ui.input("Nº de albarán ou factura (opcional)").classes("w-full")
        superficie = CampoSuperficie("Superficie colleitada (baleiro = a do cultivo)")
        data_fin = campo_data("Data de fin (se durou máis dun día)")
        horas = ui.input("Horas de traballo").classes("w-full")
```

### Paso 3 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
                        restos_no_solo=restos_solo.value,
```

Despois:
```python
                        restos_no_solo=restos_solo.value,
                        persoa_id=persoa.value,
                        horas=parsear_decimal(horas.value),
```

### Paso 4 — `src/horta/ui/pages/colleitas.py`

Antes:
```python
        data.value = (c.data if c else date.today()).isoformat()
```

Despois:
```python
        data.value = (c.data if c else date.today()).isoformat()
        persoa.value = (c.persoa_id if c.persoa_id in persoas else None) if c else (
            proposta_quen(horta_id))
        horas.value = f"{c.horas:g}" if c and c.horas else ""
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Formularios con quen (6/8): colleita: feito.
