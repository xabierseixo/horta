# Tarefa 045c — Táboas en galego (tratamentos, fertilización, animais, tarefas)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 045. **Axente**: qwen-66 (mantemento).

## Obxectivo

As táboas mostraban textos de Quasar en inglés ("Records per page", "1-1 of 1", "1 record selected"); o galego é sempre a base. `ui/taboas.py` ten os textos en galego (`TEXTOS_TABOA`) e cada táboa engádeos ás súas props. Análise 2026-10-23, A4. Esta tarefa leva o mesmo cambio á táboa de tratamentos e ás tres de `horta_detalle.py` (comparten `_PROPS_TABOA`).

## Ficheiros a tocar

- `src/horta/ui/pages/tratamentos_fito.py`
- `src/horta/ui/pages/horta_detalle.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/tratamentos_fito.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 2 — `src/horta/ui/pages/tratamentos_fito.py`: textos na táboa

Antes:
```python
        'flat bordered no-data-label="Aínda non hai tratamentos rexistrados"'
```

Despois:
```python
        f'flat bordered no-data-label="Aínda non hai tratamentos rexistrados" {TEXTOS_TABOA}'
```

### Paso 3 — `src/horta/ui/pages/horta_detalle.py`: importar

Antes:
```python
from horta.ui.superficie import CampoSuperficie
```

Despois:
```python
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 4 — `src/horta/ui/pages/horta_detalle.py`: textos nas táboas

Antes:
```python
_PROPS_TABOA = 'flat bordered no-data-label="Aínda non hai rexistros"'
```

Despois:
```python
_PROPS_TABOA = f'flat bordered no-data-label="Aínda non hai rexistros" {TEXTOS_TABOA}'
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As táboas de tratamentos, fertilización, animais e tarefas mostran os textos en galego.
