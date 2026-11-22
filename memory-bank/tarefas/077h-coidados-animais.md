# Tarefa 077h — Coidado dos animais (9/10): Animais e tempo de espera

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefas 077e e 077f. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

En Animais sae se o grupo está en tempo de espera e unha ligazón aos coidados; a sección dos coidados ábrese. Deseño: `docs/superpowers/specs/2026-10-27-coidado-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.services.catalogos_estado import avisos_catalogos
```

Despois:
```python
from horta.services.catalogos_estado import avisos_catalogos
from horta.services.coidados_animais import en_tempo_espera
```

### Paso 2 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
from horta.ui.pages.analises import seccion_analises
```

Despois:
```python
from horta.ui.pages.analises import seccion_analises
from horta.ui.pages.coidados_animais import seccion_coidados
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
        _seccion_animais(horta_id, animais, pode_editar)
```

Despois:
```python
        _seccion_animais(horta_id, animais, pode_editar)
    elif seccion == "coidados":
        seccion_coidados(horta_id, pode_editar)
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                ui.button("Cancelar", on_click=dialog_novo_animal.close).props("flat")

    with ui.row().classes("w-full items-center justify-between"):
```

Despois:
```python
                ui.button("Cancelar", on_click=dialog_novo_animal.close).props("flat")

    with get_session() as session:
        actor = usuario_actual(session)
        espera = en_tempo_espera(session, actor, horta_id) if actor else {}

    with ui.row().classes("w-full items-center justify-between"):
        ui.link("Ver os coidados dos animais", url_seccion(horta_id, "coidados"))
```

### Paso 5 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
            "estado": a.estado,
```

Despois:
```python
            "estado": a.estado,
            "espera": f"En tempo de espera ata {espera[a.id]:%d/%m/%Y}" if a.id in espera
            else "",
```

### Paso 6 — `src/horta/ui/pages/horta_detalle.py`

Antes:
```python
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
```

Despois:
```python
                {"name": "cantidade", "label": "Cantidade", "field": "cantidade"},
                {"name": "estado", "label": "Estado", "field": "estado"},
                {"name": "espera", "label": "Medicamentos", "field": "espera"},
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Coidado dos animais (9/10): Animais e tempo de espera: feito.
