# Tarefa 045b — Táboas en galego (colleitas, maquinaria, equipo)

**Estado**: feita

**Rama**: `deseno-visual`. **Depende de**: tarefa 045. **Axente**: qwen-66 (mantemento).

## Obxectivo

As táboas mostraban textos de Quasar en inglés ("Records per page", "1-1 of 1", "1 record selected"); o galego é sempre a base. `ui/taboas.py` ten os textos en galego (`TEXTOS_TABOA`) e cada táboa engádeos ás súas props. Análise 2026-10-23, A4. Esta tarefa leva o mesmo cambio a outras tres táboas.

## Ficheiros a tocar

- `src/horta/ui/pages/colleitas.py`
- `src/horta/ui/pages/maquinaria.py`
- `src/horta/ui/pages/equipo.py`

Ningún outro (agás este ficheiro da tarefa e `memory-bank/activeContext.md`). Non executes `ruff format`. Non crees scripts: fai cada paso coa ferramenta de editar ficheiros.

## Pasos

Fai cada substitución **literalmente**: busca o bloque completo de "Antes" (existe unha soa vez) e cámbiao polo de "Despois".

### Paso 1 — `src/horta/ui/pages/colleitas.py`: importar

Antes:
```python
from horta.ui.superficie import CampoSuperficie
```

Despois:
```python
from horta.ui.superficie import CampoSuperficie
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 2 — `src/horta/ui/pages/colleitas.py`: textos na táboa

Antes:
```python
        'flat bordered no-data-label="Aínda non hai colleitas"'
```

Despois:
```python
        f'flat bordered no-data-label="Aínda non hai colleitas" {TEXTOS_TABOA}'
```

### Paso 3 — `src/horta/ui/pages/maquinaria.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 4 — `src/horta/ui/pages/maquinaria.py`: textos na táboa

Antes:
```python
        'flat bordered no-data-label="Aínda non hai máquinas rexistradas"'
```

Despois:
```python
        f'flat bordered no-data-label="Aínda non hai máquinas rexistradas" {TEXTOS_TABOA}'
```

### Paso 5 — `src/horta/ui/pages/equipo.py`: importar

Antes:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
```

Despois:
```python
from horta.ui.sesion import pechar_sesion, usuario_actual
from horta.ui.taboas import TEXTOS_TABOA
```

### Paso 6 — `src/horta/ui/pages/equipo.py`: textos na táboa

Antes:
```python
        'flat bordered no-data-label="Aínda non hai ninguén no equipo"'
```

Despois:
```python
        f'flat bordered no-data-label="Aínda non hai ninguén no equipo" {TEXTOS_TABOA}'
```

## Comprobacións

```bash
uv run pytest -q
uv run ruff check src tests
uv run mypy src
```

## Resultado

As táboas de colleitas, maquinaria e equipo mostran os textos en galego.
