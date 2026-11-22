# Tarefa 045 — Táboas en galego e menú pechado no móbil

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: ningunha. **Axente**: ornith-88 (funcionalidade).

## Obxectivo

As táboas mostraban textos de Quasar en inglés ("Records per page", "1-1 of 1", "1 record selected"); o galego é sempre a base. `ui/taboas.py` ten os textos en galego (`TEXTOS_TABOA`) e cada táboa engádeos ás súas props. Análise 2026-10-23, A4. Ademais, no móbil o menú lateral abríase tapando a pantalla en cada sección (A1): con `value=False` e `show-if-above` queda aberto só en pantallas grandes.

## Ficheiros a tocar

- `src/horta/ui/taboas.py` (**ficheiro novo**)
- `src/horta/ui/pages/parcelas.py`
- `src/horta/ui/pages/cultivos.py`
- `src/horta/ui/layout.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — crear o ficheiro `src/horta/ui/taboas.py`

Contido completo:
```python
"""Textos comúns das táboas en galego (Quasar non trae galego e mostra inglés)."""

TEXTOS_TABOA = (
    'rows-per-page-label="Filas por páxina" no-results-label="Non hai resultados" '
    ':pagination-label="(primeira, ultima, total) => `${primeira}-${ultima} de ${total}`" '
    ":selected-rows-label=\"(n) => n === 1 ? '1 fila escollida' : `${n} filas escollidas`\""
)
```

### Paso 2 — `src/horta/ui/pages/parcelas.py`: importar

Antes:
```python
from horta.ui.superficie import CampoSuperficie, formatar_superficie
```

Despois:
```python
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 3 — `src/horta/ui/pages/parcelas.py`: textos na táboa

Antes:
```python
    ).classes("w-full taboa").props('flat bordered no-data-label="Aínda non hai parcelas"')
```

Despois:
```python
    ).classes("w-full taboa").props(
        f'flat bordered no-data-label="Aínda non hai parcelas" {TEXTOS_TABOA}')
```

### Paso 4 — `src/horta/ui/pages/cultivos.py`: importar

Antes:
```python
from horta.ui.superficie import CampoSuperficie, formatar_superficie
```

Despois:
```python
from horta.ui.superficie import CampoSuperficie, formatar_superficie
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 5 — `src/horta/ui/pages/cultivos.py`: textos na táboa

Antes:
```python
        'flat bordered no-data-label="Aínda non hai cultivos"'
```

Despois:
```python
        f'flat bordered no-data-label="Aínda non hai cultivos" {TEXTOS_TABOA}'
```

### Paso 6 — `src/horta/ui/layout.py`: menú pechado no móbil

Antes:
```python
    menu = ui.left_drawer(value=True, fixed=True).props(
```

Despois:
```python
    menu = ui.left_drawer(value=False, fixed=True).props(
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As táboas de parcelas e cultivos mostran os textos en galego; no móbil o menú xa non tapa a pantalla ao entrar.
