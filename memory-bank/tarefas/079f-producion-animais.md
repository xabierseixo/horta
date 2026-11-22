# Tarefa 079f — Produción dos animais (7/11): botón en Animais

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 079e. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

Botón «Produción» no grupo de animais, que abre o formulario co grupo escollido, e ligazón «Ver a produción». Deseño: `docs/superpowers/specs/2026-10-28-producion-animais-design.md`

## Ficheiros a tocar

- `src/horta/ui/pages/animais.py`

Ningún outro (agás este ficheiro da tarefa; calquera outro cambio desfaise ao integrar). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/animais.py`

Antes:
```python
"""Sección Animais: os grupos de animais. A cantidade sae das entradas e saídas; os coidados e
os movementos teñen as súas táboas."""
```

Despois:
```python
"""Sección Animais: os grupos de animais. A cantidade sae das entradas e saídas; os coidados,
os movementos e a produción teñen as súas táboas."""
```

### Paso 2 — `src/horta/ui/pages/animais.py`

Antes:
```python
from horta.ui.pages.movementos_animais import dialogo_movemento
```

Despois:
```python
from horta.ui.pages.movementos_animais import dialogo_movemento
from horta.ui.pages.producions_animais import dialogo_producion
```

### Paso 3 — `src/horta/ui/pages/animais.py`

Antes:
```python
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))
```

Despois:
```python
        ui.link("Ver os coidados", url_seccion(horta_id, "coidados"))
        ui.link("Ver a produción", url_seccion(horta_id, "producion"))
```

### Paso 4 — `src/horta/ui/pages/animais.py`

Antes:
```python
    abrir_movemento = dialogo_movemento(horta_id)
```

Despois:
```python
    abrir_movemento = dialogo_movemento(horta_id)
    abrir_producion = dialogo_producion(horta_id)
```

### Paso 5 — `src/horta/ui/pages/animais.py`

Antes:
```python
        abrir_movemento(None, None, taboa.selected[0]["id"] if taboa.selected else None)

```

Despois:
```python
        abrir_movemento(None, None, taboa.selected[0]["id"] if taboa.selected else None)

    def producion() -> None:
        abrir_producion(None, None, taboa.selected[0]["id"] if taboa.selected else None)

```

### Paso 6 — `src/horta/ui/pages/animais.py`

Antes:
```python
        ui.button("Entrada ou saída", icon="swap_horiz", on_click=movemento).props("outline")
```

Despois:
```python
        ui.button("Entrada ou saída", icon="swap_horiz", on_click=movemento).props("outline")
        ui.button("Produción", icon="egg", on_click=producion).props("outline")
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

Produción dos animais (7/11): botón en Animais: feito.
